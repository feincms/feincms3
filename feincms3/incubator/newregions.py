from collections import deque
from functools import wraps

from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe

from content_editor.contents import contents_for_item


class Regions:
    @classmethod
    def from_contents(cls, contents, *, renderer):
        return cls(contents=contents, renderer=renderer)

    @classmethod
    def from_item(cls, item, *, renderer, inherit_from=None):
        return cls(
            contents=SimpleLazyObject(
                lambda: contents_for_item(
                    item, renderer.plugins(), inherit_from=inherit_from
                )
            ),
            renderer=renderer,
        )

    def __init__(self, *, contents, renderer):
        self.contents = contents
        self.renderer = renderer

    def render(self, region, context=None, **kwargs):
        return mark_safe(
            "".join(
                self.renderer.render_plugin_in_context(item, context)
                for item in self.contents[region]
            )
        )


class SectionRegions(Regions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.__class__, "sections"):
            self.__class__.sections = {
                key[7:]: getattr(self, key)
                for key in dir(self.__class__)
                if key.startswith("handle_")
            }

    def render(self, region, context=None, **kwargs):
        def _generator(items):
            while items:
                if hasattr(items[0], "section"):
                    handler = self.sections.get(items[0].section)
                    if handler:
                        yield from handler(items, context)
                        continue
                yield self.renderer.render_plugin_in_context(items.popleft(), context)

        return mark_safe("".join(_generator(deque(self.contents[region]))))


def matches(item, *, plugins=None, sections=None):
    if plugins is not None and not isinstance(item, plugins):
        return False
    if (
        sections is not None
        and hasattr(item, "section")
        and getattr(item, "section") not in sections
    ):
        return False
    return True


def wrap_section(start, end):
    def dec(fn):
        @wraps(fn)
        def _dec(*args, **kwargs):
            yield start
            yield from fn(*args, **kwargs)
            yield end

        return _dec

    return dec
