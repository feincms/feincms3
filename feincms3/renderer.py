from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe

from content_editor.contents import contents_for_item


__all__ = ('TemplatePluginRenderer',)


def default_context(plugin, context):
    return {'plugin': plugin}


class Regions(object):
    def __init__(self, item, contents, renderer):
        self._item = item
        self._contents = contents
        self._renderer = renderer

    def cache_key(self, region):
        return '%s-%s-%s' % (
            self._item._meta.label_lower,
            self._item.pk,
            region,
        )

    def render(self, region, context, timeout=None):
        if timeout is not None:
            key = self.cache_key(region)
            html = cache.get(key)
            if html is not None:
                return html

        html = mark_safe(''.join(
            self._renderer.render_plugin_in_context(plugin, context)
            for plugin in self._contents[region]
        ))

        if timeout is not None:
            cache.set(key, html, timeout=timeout)
        return html


class TemplatePluginRenderer(object):
    """
    More capable replacement for django-content-editor_'s ``PluginRenderer``

    Allows passing the full template rendering context to plugins, but does
    not have any autodetection of rendering methods. The exact model classes
    have to be registered with this renderer.

    Usage example::

        renderer = TemplatePluginRenderer()

    """

    def __init__(self):
        self._renderers = {}

    def register_string_renderer(self, plugin, renderer):
        """
        Register a rendering function which is passed the plugin instance and
        returns a HTML string::

            renderer.register_string_renderer(
                RichText,
                lambda plugin: mark_safe(plugin.text),
            )
        """
        self._renderers[plugin] = (None, renderer)

    def register_template_renderer(self, plugin, template_name, context=None):
        """
        Register a renderer for ``plugin`` using a template. The template uses
        the same mechanism as ``{% include %}`` meaning that the full template
        context is available to the plugin renderer.

        ``template_name`` can be one of:

        - A template path
        - A list of template paths
        - An object with a ``render`` method
        - A callable receiving the plugin as only parameter and returning any
          of the above.

        ``context`` may be ``None``, a dictionary, or a callable receiving the
        plugin instance and the template context and returning a dictionary.

        Usage::

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
        self._renderers[plugin] = (template_name, context or default_context)

    def plugins(self):
        """
        Return a list of all registered plugins, and is most useful when passed
        directly to one of django-content-editor_'s contents utilities::

            page = get_object_or_404(Page, ...)
            contents = contents_for_item(page, renderer.plugins())

        """

        return list(self._renderers.keys())

    def regions(self, item, inherit_from=None, regions=Regions):
        return regions(
            item,
            SimpleLazyObject(
                lambda: contents_for_item(item, self.plugins(), inherit_from)
            ),
            self,
        )

    def render_plugin_in_context(self, plugin, context):
        """
        Render a plugin, passing on the template context into the plugin's
        template (if the plugin uses a template renderer).

        The template tags in ``feincms3_renderer`` assume that the renderer
        instance is available as ``renderer`` inside the context. A suitable
        view would look as follows::

            def page_detail(request, slug):
                page = get_object_or_404(Page, slug=slug)
                return render(request, 'page.html', {
                    'page': page,
                    'contents': contents_for_item(page, renderer.plugins()),
                    'renderer': renderer,
                })

        The template itself should contain the following snippet::

            {% load feincms3_renderer %}

            {% block content %}

            <h1>{{ page.title }}</h1>
            <main>
              {% for plugin in contents.main %}
                {% render_plugin plugin %}
              {% endfor %}
            </main>
            <aside>
              {# or simply #}
              {% render_plugins contents.sidebar %}
            </aside>

            {% endblock %}
        """
        engine = context.template.engine
        plugin_template, plugin_context = self._renderers[plugin.__class__]

        if plugin_template is None:
            return plugin_context(plugin)  # Simple string renderer

        if callable(plugin_template):
            plugin_template = plugin_template(plugin)
        if callable(plugin_context):
            plugin_context = plugin_context(plugin, context)

        if not hasattr(plugin_template, 'render'):  # Quacks like a template?
            if isinstance(plugin_template, (list, tuple)):
                plugin_template = engine.select_template(plugin_template)
            else:
                plugin_template = engine.get_template(plugin_template)

        with context.push(plugin_context):
            return plugin_template.render(context)
