from collections import deque
from functools import wraps

from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe

from content_editor.contents import contents_for_item


__all__ = ("Regions", "matches", "cached_render")


def item_cache_key(item):
    return lambda region: "%s-%s-%s" % (item._meta.label_lower, item.pk, region)


def cached_render(fn):
    @wraps(fn)
    def render(self, region, context=None):
        if self.cache_key:
            key = self.cache_key(region)
            result = cache.get(key)
            if result is not None:
                return result
        result = fn(self, region, context)
        # result = mark_safe("".join(self.generate(self.contents[region], context)))
        if self.cache_key:
            cache.set(key, result, timeout=self.timeout)
        return result

    return render


class Regions:
    @classmethod
    def from_contents(cls, contents, **kwargs):
        return cls(contents=contents, **kwargs)

    @classmethod
    def from_item(cls, item, *, renderer, inherit_from=None, timeout=None, **kwargs):
        return cls.from_contents(
            SimpleLazyObject(
                lambda: contents_for_item(
                    item, renderer.plugins(), inherit_from=inherit_from
                )
            ),
            renderer=renderer,
            cache_key=None if timeout is None else item_cache_key(item),
            timeout=timeout,
            **kwargs
        )

    def __init__(self, *, contents, renderer, cache_key=None, timeout=None):
        self.contents = contents
        self.renderer = renderer
        self.cache_key = cache_key
        self.timeout = timeout
        self.handlers = {
            key[7:]: getattr(self, key)
            for key in dir(self)
            if key.startswith("handle_")
        }

    @cached_render
    def render(self, region, context=None):
        return mark_safe("".join(self.generate(self.contents[region], context)))

    def generate(self, items, context):
        items = deque(items)
        while items:
            subregion = getattr(items[0], "subregion", None) or "default"
            yield from self.handlers[subregion](items, context)

    def handle_default(self, items, context):
        while True:
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
            if not items or not matches(items[0], subregions={}):
                break


def matches(item, *, plugins=None, subregions=None):
    if plugins is not None and not isinstance(item, plugins):
        return False
    if (
        subregions is not None
        and hasattr(item, "subregion")
        and getattr(item, "subregion") not in subregions
    ):
        return False
    return True
