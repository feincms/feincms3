"""
.. warning::
   This module is deprecated. Use :mod:`feincms3.renderer.RegionRenderer`
   instead.
"""

import warnings
from collections import deque
from functools import wraps

from content_editor.contents import contents_for_item
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe


__all__ = ("Regions", "matches", "cached_render")


warnings.warn(
    "feincms3.regions is deprecated. Switch to feincms3.renderer.RegionRenderer now.",
    DeprecationWarning,
    stacklevel=2,
)


def cached_render(fn):
    """
    Decorator for ``Regions.render`` methods implementing caching behavior
    """

    @wraps(fn)
    def render(self, region, context=None):
        key = self.cache_key(region) if self.cache_key else None
        if key:
            result = cache.get(key)
            if result is not None:
                return result
        result = fn(self, region, context)
        if key:
            cache.set(key, result, timeout=self.timeout)
        return result

    return render


class Regions:
    """
    ``Regions`` uses ``content_editor.contents.Contents`` and the
    ``feincms3.renderer.TemplatePluginRenderer`` to convert a list of plugins
    into a rendered representation, most often a HTML fragment.

    This class may also be instantiated directly but using the factory methods
    (starting with ``from_``) below is probably more comfortable.
    """

    @classmethod
    def from_contents(cls, contents, *, renderer, **kwargs):
        """
        Create and return a regions instance using the bare minimum of a
        contents instance and a renderer. Additional keyword arguments are
        forwarded to the regions constructor.
        """
        return cls(contents=contents, renderer=renderer, **kwargs)

    @classmethod
    def from_item(cls, item, *, renderer, inherit_from=None, timeout=None, **kwargs):
        """
        Create and return a regions instance for an item (for example a page,
        an article or anything else managed by django-content-editor).

        The item's plugins are determined by what is registered with the
        renderer. The plugin instances themselves are loaded lazily, and
        loading every time can be avoided completely by specifying a
        ``timeout``.
        """
        if timeout is not None and "cache_key" not in kwargs:
            key = f"{item._meta.label_lower}-{item.pk}"
            kwargs["cache_key"] = lambda region: f"{key}-{region}"
        return cls.from_contents(
            SimpleLazyObject(
                lambda: contents_for_item(
                    item, renderer.plugins(), inherit_from=inherit_from
                )
            ),
            renderer=renderer,
            timeout=timeout,
            **kwargs,
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

    @property
    def regions(self):
        return self.contents.regions

    @cached_render
    def render(self, region, context=None):
        """
        Main function for rendering.

        Starts the generator and assembles all fragments into a safe HTML
        string.
        """
        return mark_safe("".join(self.generate(self.contents[region], context)))

    def generate(self, items, context):
        """
        Inspects all items in the region for a  ``subregion`` attribute and
        passes control to the subregions' respective rendering handler, named
        ``handle_<subregion>``. If ``subregion`` is not set or is falsy
        ``handle_default`` is invoked instead. This method raises a
        ``KeyError`` exception if no matching handler exists.

        You probably want to call this method when overriding ``render``.
        """
        items = deque(items)
        while items:
            subregion = getattr(items[0], "subregion", None) or "default"
            yield from self.handlers[subregion](items, context)

    def handle_default(self, items, context):
        """
        Renders items from the queue using the renderer instance as long as the
        items either have no ``subregion`` attribute or whose ``subregion``
        attribute is an empty string.
        """
        while True:
            yield self.renderer.render_plugin(items.popleft(), context)
            if not items or not matches(items[0], subregions={None, ""}):
                break


def matches(item, *, plugins=None, subregions=None):
    """
    Checks whether the item matches zero or more constraints.

    ``plugins`` should be a tuple of plugin classes or ``None`` if the type
    shouldn't be checked.

    ``subregions`` should be set of allowed ``subregion`` attribute values or
    ``None`` if the ``subregion`` attribute shouldn't be checked at all.
    Include ``None`` in the set if you want ``matches`` to succeed also when
    encountering an item without a ``subregion`` attribute.
    """
    if plugins is not None and not isinstance(item, plugins):
        return False
    if subregions is not None and getattr(item, "subregion", None) not in subregions:
        return False
    return True
