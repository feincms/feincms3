from django import template
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def render_plugin(context, plugin):
    """
    Render a single plugin. Requires the
    :class:`feincms3.renderer.TemplatePluginRenderer` instance in the context
    as ``renderer``::

        {% render_plugin plugin %}

    In general you should prefer
    :func:`~feincms3.templatetags.feincms3_renderer.render_region` over this
    tag.
    """
    return context["renderer"].render_plugin_in_context(plugin, context)


@register.simple_tag(takes_context=True)
def render_plugins(context, plugins):
    """
    Render a list of plugins. Requires the
    :class:`feincms3.renderer.TemplatePluginRenderer` instance in the context
    as ``renderer``::

        {% render_plugins plugins %}

    This plugin is equivalent to::

        {% for plugin in plugins %}{% render_plugin plugin %}{% endfor %}

    In general you should prefer
    :func:`~feincms3.templatetags.feincms3_renderer.render_region` over this
    tag.
    """
    renderer = context["renderer"]
    return mark_safe(
        "".join(
            renderer.render_plugin_in_context(plugin, context) for plugin in plugins
        )
    )


@register.simple_tag(takes_context=True)
def render_region(context, regions, region, **kwargs):
    """
    Render a single region. See :class:`~feincms3.renderer.Regions` for
    additional details. Any and all keyword arguments are forwarded to the
    ``render`` method of the ``Regions`` instance.

    Usage::

        {% render_region regions "main" %}

    and::

        {% render_region regions "main" timeout=15 %}

    The main advantage of :class:`~feincms3.renderer.Regions` and
    ``render_region`` is that regions only lazily load plugins when needed,
    which means that caching also avoids the related database queries.
    """
    return regions.render(region, context, **kwargs)
