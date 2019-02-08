import warnings
from functools import wraps

from django.core.cache import cache
from django.template import Context, Engine
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe

from content_editor.contents import contents_for_item


__all__ = ("TemplatePluginRenderer", "Regions", "cached_render", "default_context")


class PluginNotRegistered(Exception):
    pass


def default_context(plugin, context):
    """
    Return the default context for plugins rendered with a template, which
    simply is a single variable named ``plugin`` containing the plugin
    instance.
    """
    return {"plugin": plugin}


def cached_render(fn):
    """
    Decorator for ``Regions.render`` methods implementing caching behavior

    This decorator consumes the ``timeout`` keyword argument to the ``render``
    method.
    """

    @wraps(fn)
    def render(self, region, context=None, *, timeout=None, **kwargs):
        if timeout is None:
            return fn(self, region, context=context, **kwargs)

        key = self.cache_key(region)
        html = cache.get(key)
        if html is not None:
            return html
        html = fn(self, region, context=context, **kwargs)
        cache.set(key, html, timeout=timeout)
        return html

    return render


class Regions:
    """Regions(*, item, contents, renderer)

    .. note::
       ``feincms3.renderer.Regions`` has been deprecated in favor of
       :class:`feincms3.regions.Regions`.
    Wrapper for a ``content_editor.contents.Contents`` instance with support
    for caching the potentially somewhat expensive plugin loading and rendering
    step.

    A view using this facility would look as follows::

        def page_detail(request, slug):
            page = get_object_or_404(Page, slug=slug)
            return render(request, 'page.html', {
                'page': page,
                'regions': renderer.regions(
                    page,
                    # Optional:
                    inherit_from=page.ancestors().reverse(),
                    # Optional too:
                    timeout=15,
                ),
                # Note! No 'contents' and no 'renderer' necessary in the
                # template.
            })

    The template itself should contain the following snippet::

        {% load feincms3 %}

        {% block content %}

        <h1>{{ page.title }}</h1>
        <main>
          {% render_region regions "main" timeout=60 %}
        </main>
        <aside>
          {% render_region regions "sidebar" timeout=60 %}
        </aside>

        {% endblock %}

    Caching is, of course, completely optional. When you're caching regions
    though you should probably cache them all, because accessing the content of
    a single region loads the content of all regions. (It might still make
    sense if the rendering is the expensive part, not the database access.)

    .. note::
       You should probably always let the renderer instantiate this class and
       not depend on the API, especially since the lazyness happens in the
       renderer, not in the ``Regions`` instance.
    """

    def __init__(self, item, *, contents, renderer):
        self._item = item
        self._contents = contents
        self._renderer = renderer

    def cache_key(self, region):
        """
        Return a cache key suitable for the given ``region`` passed
        """
        return "%s-%s-%s" % (self._item._meta.label_lower, self._item.pk, region)

    @cached_render
    def render(self, region, context=None):
        """render(self, region, context=None, *, timeout=None)
        Render a single region using the context passed

        If ``timeout`` is ``None`` caching is disabled.
        """
        return mark_safe(
            "".join(
                self._renderer.render_plugin_in_context(plugin, context)
                for plugin in self._contents[region]
            )
        )


class TemplatePluginRenderer:
    """
    This renderer allows registering functions, templates and context providers
    for plugins. It also supports rendering plugins' templates using the
    rendering context of the surrounding template without explicitly copying
    required values into the local rendering context.
    """

    def __init__(self, *, regions_class=Regions):
        self._renderers = {}
        self._regions_class = regions_class

    def register_string_renderer(self, plugin, renderer):
        """
        Register a rendering function which is passed the plugin instance and
        returns a HTML string:

        .. code-block:: python

            renderer.register_string_renderer(
                RichText,
                lambda plugin: mark_safe(plugin.text),
            )
        """
        self._renderers[plugin] = (None, renderer)

    def register_template_renderer(
        self, plugin, template_name, context=default_context
    ):
        """register_template_renderer(self, plugin, template_name,\
context=default_context)
        Register a renderer for ``plugin`` using a template. The template uses
        the same mechanism as ``{% include %}`` meaning that the full template
        context is available to the plugin renderer.

        ``template_name`` can be one of:

        - A template path
        - A list of template paths
        - An object with a ``render`` method
        - A callable receiving the plugin as only parameter and returning any
          of the above.

        ``context`` must be a callable receiving the plugin instance and the
        template context and returning a dictionary. The default implementation
        simply returns a dictionary containing a single key named ``plugin``
        containing the plugin instance.

        .. code-block:: python

            # Template snippets have access to everything in the template
            # context, including for example ``page``, ``request``, etc.
            renderer.register_template_renderer(
                Snippet,
                lambda plugin: plugin.template_name,
            )

            # Additional context can be provided:
            renderer.register_template_renderer(
                Team,
                'pages/plugins/team.html',  # Can also be a callable
                lambda plugin, context: {
                    'persons': Person.objects.filter(
                        # Assuming that the page has a team foreign key:
                        team=plugin.parent.team,
                    ),
                },
            )
        """
        self._renderers[plugin] = (template_name, context)

    def plugins(self):
        """
        Return a list of all registered plugins, and is most useful when passed
        directly to one of django-content-editor's contents utilities:

        .. code-block:: python

            page = get_object_or_404(Page, ...)
            contents = contents_for_item(page, renderer.plugins())
        """

        return list(self._renderers.keys())

    def regions(self, item, *, inherit_from=None, regions=None):
        """
        Return a ``Regions`` instance which lazily wraps the
        ``contents_for_item`` call. This is especially useful in conjunction
        with the ``render_region`` template tag. The ``inherit_from`` argument
        is directly forwarded to ``contents_for_item`` to allow regions with
        inherited content.

        The ``Regions`` type may be overridden by passing a ``regions_class``
        keyword argument when instantiating the ``TemplatePluginRenderer`` or
        by setting the ``regions`` argument of this method.
        """
        warnings.warn(
            "TemplatePluginRenderer.regions() will be removed. Please"
            " start using feincms3.regions.Regions.from_item() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        regions = self._regions_class if regions is None else regions
        return regions(
            item=item,
            contents=SimpleLazyObject(
                lambda: contents_for_item(item, self.plugins(), inherit_from)
            ),
            renderer=self,
        )

    def render_plugin_in_context(self, plugin, context=None):
        """
        Render a plugin, passing on the template context into the plugin's
        template (if the plugin uses a template renderer).
        """
        if plugin.__class__ not in self._renderers:
            raise PluginNotRegistered(
                "Plugin %s is not registered" % plugin._meta.label_lower
            )
        plugin_template, plugin_context = self._renderers[plugin.__class__]

        if plugin_template is None:
            return (
                plugin_context(plugin) if callable(plugin_context) else plugin_context
            )  # Simple string renderer

        if context is None:
            context = Context()

        if callable(plugin_template):
            plugin_template = plugin_template(plugin)
        if callable(plugin_context):
            plugin_context = plugin_context(plugin, context)

        if not hasattr(plugin_template, "render"):  # Quacks like a template?
            try:
                engine = context.template.engine
            except AttributeError:
                engine = Engine.get_default()

            if isinstance(plugin_template, (list, tuple)):
                plugin_template = engine.select_template(plugin_template)
            else:
                plugin_template = engine.get_template(plugin_template)

        with context.push(plugin_context):
            return plugin_template.render(context)
