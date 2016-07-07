from __future__ import unicode_literals


__all__ = ('TemplatePluginRenderer',)


class TemplatePluginRenderer(object):
    """
    More capable replacement for django-content-editor_'s ``PluginRenderer``

    Allows passing the full template rendering context to plugins, but does
    not have any autodetection of rendering methods. The exact model classes
    have to be registered with this renderer.

    Usage example::

        renderer = TemplatePluginRenderer()

        # Also support rendering plugins whose renderers simply return a
        # HTML string.
        renderer.register_string_renderer(
            RichText,
            lambda plugin: mark_safe(plugin.text),
        )

        # Template snippets have access to everything in the template context,
        # including for example ``page``, ``request``, etc.
        renderer.register_template_renderer(
            Snippet,
            template_name=lambda plugin: plugin.template_name,
        )

        # Additional context can be provided:
        renderer.register_template_renderer(
            Team,
            'pages/plugins/team.html',
            lambda plugin, context: {
                'persons': Person.objects.filter(
                    team=plugin.parent.team,  # Assuming that the page has a
                                              # team foreign key.
                ),
            },
        )

    The template tags in ``feincms3_renderer`` assume that the renderer
    instance is available as ``renderer`` inside the template::

        def page_detail(request, slug):
            page = get_object_or_404(Page, slug=slug)
            return render(request, 'page.html', {
                'page': page,
                'contents': contents_for_item(page, renderer.plugins()),
                'renderer': renderer,
            })

    And inside the template::

        {% load feincms3_renderer %}

        <h1>{{ page.title }}</h1>
        {% for plugin in contents.main %}
            {% render_plugin plugin %}
        {% endfor %}
        {# or simply #}
        {% render_plugins contents.sidebar %}
    """

    def __init__(self):
        self._renderers = {}

    def plugins(self):
        return list(self._renderers.keys())

    def register_string_renderer(self, plugin, renderer):
        """
        Register a rendering function which is passed the plugin instance and
        returns a HTML string.
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
        - An object with a ``render`` function
        - A callable receiving the plugin as only parameter and returning any
          of the above.

        ``context`` may be ``None``, a dictionary, or a callable receiving the
        plugin instance and the template context and returning a dictionary.
        """
        self._renderers[plugin] = (template_name, context or {})

    def render_plugin_in_context(self, plugin, context):
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
