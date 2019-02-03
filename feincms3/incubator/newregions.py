from collections import deque

from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe

from content_editor.contents import contents_for_item


class Regions:
    @classmethod
    def from_contents(cls, contents, *, renderer):
        return cls(contents=contents, renderer=renderer)

    @classmethod
    def from_item(cls, item, *, renderer, inherit_from=None):
        return cls.from_contents(
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
        self.handlers = {
            key[7:]: getattr(self, key)
            for key in dir(self)
            if key.startswith("handle_")
        }

    def render(self, region, context=None, **kwargs):
        return mark_safe("".join(self.generate(self.contents[region], context)))

    def generate(self, items, context):
        items = deque(items)
        while items:
            section = getattr(items[0], "section", None) or "default"
            yield from self.handlers[section](items, context)

    def handle_default(self, items, context):
        while True:
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
            if not items or not matches(items[0], sections={}):
                break


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
