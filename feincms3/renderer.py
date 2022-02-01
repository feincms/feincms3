import warnings
from collections import deque

from content_editor.contents import contents_for_item
from django.core.cache import cache
from django.template import Context, Engine
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe


__all__ = (
    "PluginNotRegistered",
    "RegionRenderer",
    "TemplatePluginRenderer",
    "default_context",
    "render_in_context",
    "template_renderer",
)


class PluginNotRegistered(Exception):
    pass


def default_context(plugin, context):
    """
    Return the default context for plugins rendered with a template, which
    simply is a single variable named ``plugin`` containing the plugin
    instance.
    """
    return {"plugin": plugin}


def render_in_context(context, template, local_context=None):
    """Render using a template rendering context

    This utility avoids the problem of ``render_to_string`` requiring a
    ``dict`` and not a full-blown ``Context`` instance which would needlessly
    burn CPU cycles."""

    if context is None:
        context = Context()

    if not hasattr(template, "render"):  # Quacks like a template?
        try:
            engine = context.template.engine
        except AttributeError:
            engine = Engine.get_default()

        if isinstance(template, (list, tuple)):
            template = engine.select_template(template)
        else:
            template = engine.get_template(template)

    with context.push(local_context):
        return template.render(context)


def template_renderer(template_name, local_context=default_context, /):
    return lambda item, context: render_in_context(
        context, template_name, local_context(item, context)
    )


class RegionRenderer:
    def __init__(self):
        self._renderers = {}
        self._subregions = {}

    def register(self, plugin, renderer, /, subregion=""):
        self._renderers[plugin] = renderer
        self._subregions[plugin] = subregion

        self.handlers = {
            key[7:]: getattr(self, key)
            for key in dir(self)
            if key.startswith("handle_")
        }

    def plugins(self):
        return list(self._renderers)

    def render_item(self, item, context):
        try:
            renderer = self._renderers[item.__class__]
        except KeyError:
            raise PluginNotRegistered(
                f"Plugin {item._meta.label_lower} is not registered"
            )
        if callable(renderer):
            return renderer(item, context)
        return renderer

    def subregion(self, item):
        try:
            subregion = self._subregions[item.__class__]
        except KeyError:
            raise PluginNotRegistered(
                f"Plugin {item._meta.label_lower} is not registered"
            )
        if callable(subregion):
            return subregion(item) or "default"
        return subregion or "default"

    def takewhile(self, items, *, subregion):
        while items and self.subregion(items[0]) == subregion:
            yield items.popleft()

    def handle(self, items, context):
        """
        Runs the ``handle_<subregion>`` handler for the head of the ``items``
        deque.

        This method requires that a matching handler for all values returned by
        ``self.subregion()`` exists.

        You probably want to call this method when overriding the rendering of
        a complete region.
        """
        items = deque(items)
        while items:
            yield from self.handlers[self.subregion(items[0])](items, context)

    def handle_default(self, items, context):
        """
        Renders items from the queue as long as there are items belonging to
        the ``default`` subregion.
        """
        while True:
            yield self.render_item(items.popleft(), context)
            if not items or self.subregion(items[0]) != "default":
                break

    def render_region(self, *, region, contents, context):
        return mark_safe("".join(self.handle(contents[region.key], context)))

    def regions_from_contents(self, contents, **kwargs):
        return _Regions(contents=contents, renderer=self, **kwargs)

    def regions_from_item(self, obj, /, *, inherit_from=None, timeout=None, **kwargs):
        if timeout and kwargs.get("cache_key") is None:
            kwargs["cache_key"] = f"regions-{obj._meta.label_lower}-{obj.pk}"

        contents = SimpleLazyObject(
            lambda: contents_for_item(obj, self.plugins(), inherit_from=inherit_from)
        )
        return self.regions_from_contents(contents, timeout=timeout, **kwargs)


class _Regions:
    def __init__(self, *, contents, renderer, cache_key=None, timeout=None):
        self._contents = contents
        self._renderer = renderer
        self._cache_key = cache_key
        self._timeout = timeout

    def _rendered(self, context):
        caching = self._cache_key and self._timeout
        if caching and (result := cache.get(self._cache_key)):
            return result
        result = {
            region.key: self._renderer.render_region(
                region=region, contents=self._contents, context=context
            )
            for region in self.regions
        }
        if caching:
            cache.set(self._cache_key, result, timeout=self._timeout)
        return result

    @property
    def regions(self):
        return self._contents.regions

    def render(self, region_key, context):
        rendered = self._rendered(context=context)
        return rendered.get(region_key, "")


def _compat_template_renderer(_tpl, _ctx=default_context, /):
    def renderer(item, context):
        template_name = _tpl(item) if callable(_tpl) else _tpl
        local_context = _ctx(item, context) if callable(_ctx) else _ctx
        return render_in_context(context, template_name, local_context)

    return renderer


class TemplatePluginRenderer(RegionRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            "TemplatePluginRenderer is deprecated. Switch to the RegionRenderer now.",
            DeprecationWarning,
            stacklevel=2,
        )

    def register_string_renderer(self, plugin, renderer):
        if callable(renderer):
            self.register(plugin, lambda plugin, context: renderer(plugin))
        else:
            self.register(plugin, renderer)

    def register_template_renderer(
        self, plugin, template_name, context=default_context
    ):
        self.register(plugin, _compat_template_renderer(template_name, context))

    def render_plugin_in_context(self, plugin, context=None):
        return self.render_item(plugin, context)
