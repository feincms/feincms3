from django import template
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def render_plugin(context, plugin):
    """
    Render a single plugin. See :mod:`feincms3.renderer` for additional
    details.
    """
    return context['renderer'].render_plugin_in_context(plugin, context)


@register.simple_tag(takes_context=True)
def render_plugins(context, plugins):
    """
    Render and concatenate a list of plugins. See
    :mod:`feincms3.renderer` for additional details.
    """
    renderer = context['renderer']
    return mark_safe(''.join(
        renderer.render_plugin_in_context(plugin, context)
        for plugin in plugins
    ))


@register.simple_tag(takes_context=True)
def render_region(context, regions, region, **kwargs):
    """
    Render a single region. See :mod:`feincms3.renderer` for additional
    details.
    """
    return regions.render(region, context, **kwargs)
