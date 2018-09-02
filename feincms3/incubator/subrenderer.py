from django.utils.html import mark_safe

from feincms3.renderer import Regions, TemplatePluginRenderer, cached_render
from feincms3.utils import positional


class Subrenderer(TemplatePluginRenderer):
    def accepts(self, plugin, context=None):
        return plugin.__class__ in self._renderers

    @positional(1)
    def enter(self, **kwargs):
        return ""

    @positional(1)
    def exit(self, **kwargs):
        return ""


class SubrendererRegions(Regions):
    subrenderers = {}
    current = None

    def activate(self, subrenderer, **kwargs):
        if self.current:
            yield self.current.exit(**kwargs)
        self.current = subrenderer
        if self.current:
            yield self.current.enter(**kwargs)

    @cached_render
    def render(self, region, context=None):
        output = []

        for plugin in self._contents[region]:
            if hasattr(plugin, "subrenderer"):
                new = (
                    self.subrenderers[plugin.subrenderer]
                    if plugin.subrenderer
                    else None
                )
                if new != self.current:  # Move to different subrenderer?
                    output.extend(
                        self.activate(
                            new, plugin=plugin, context=context, region=region
                        )
                    )

            if self.current:
                if self.current.accepts(plugin, context):
                    output.append(
                        self.current.render_plugin_in_context(plugin, context)
                    )
                    continue  # Subrenderer success! Process next plugin.
                else:
                    output.extend(self.activate(None, context=context, region=region))

            # No current subrenderer. Use main renderer.
            output.append(self._renderer.render_plugin_in_context(plugin, context))

        output.extend(self.activate(None, context=context, region=region))
        return mark_safe("".join(output))
