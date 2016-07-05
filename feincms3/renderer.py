from __future__ import unicode_literals


__all__ = ('TemplatePluginRenderer',)


class TemplatePluginRenderer(object):
    def __init__(self):
        self._renderers = {}

    def plugins(self):
        return list(self._renderers.keys())

    def register_string_renderer(self, plugin, renderer):
        self._renderers[plugin] = (None, renderer)

    def register_template_renderer(self, plugin, template_name, context=None):
        self._renderers[plugin] = (template_name, context or {})

    def render_plugin_in_context(self, plugin, context):
        engine = context.template.engine
        plugin_template, plugin_context = self._renderers[plugin.__class__]

        if plugin_template is None:
            return plugin_context(plugin)  # Simple string renderer

        if callable(plugin_template):
            plugin_template = plugin_template(plugin)
        if callable(plugin_context):
            plugin_context = plugin_context(plugin)

        if not hasattr(plugin_template, 'render'):  # Quacks like a template?
            if isinstance(plugin_template, (list, tuple)):
                plugin_template = engine.select_template(plugin_template)
            else:
                plugin_template = engine.get_template(plugin_template)

        with context.push(plugin_context):
            return plugin_template.render(context)
