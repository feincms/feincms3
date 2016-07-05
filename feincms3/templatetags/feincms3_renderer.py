from __future__ import unicode_literals

from django import template
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def render_plugin(context, plugin):
    return context['renderer'].render_plugin_in_context(plugin, context)


@register.simple_tag(takes_context=True)
def render_plugins(context, plugins):
    renderer = context['renderer']
    return mark_safe(''.join(
        renderer.render_plugin_in_context(plugin, context)
        for plugin in plugins
    ))
