from django import template
from django.template.base import Node, TemplateSyntaxError, kwarg_re
from django.utils.html import conditional_escape

from feincms3 import apps


register = template.Library()


@register.simple_tag(takes_context=True)
def render_region(context, regions, region, **kwargs):
    """
    Render a single region. See :class:`~feincms3.regions.Regions` for
    additional details. Any and all keyword arguments are forwarded to the
    ``render`` method of the ``Regions`` instance.

    Usage::

        {% render_region regions "main" %}
    """
    return regions.render(region, context, **kwargs)


class ReverseAppNode(Node):
    def __init__(self, namespaces, view_name, args, kwargs, asvar):
        self.namespaces = namespaces
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def _current_app(self, context):
        try:
            return context.request.current_app
        except AttributeError:
            try:
                return context.request.resolver_match.namespace
            except AttributeError:
                return None

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        namespaces = self.namespaces.resolve(context)
        view_name = self.view_name.resolve(context)
        fallback = kwargs.pop("fallback", None)
        if not isinstance(namespaces, (list, tuple)):
            namespaces = namespaces.split(",")
        # Try to look up the URL. If it fails, raise NoReverseMatch unless the
        # {% reverse ... as var %} construct is used, in which case return
        # nothing.
        url = ""
        try:
            url = apps.reverse_app(
                namespaces,
                view_name,
                args=args,
                kwargs=kwargs,
                current_app=self._current_app(context),
            )
        except apps.NoReverseMatch:
            if fallback is not None:
                url = fallback
            elif self.asvar is None:
                raise

        if self.asvar:
            context[self.asvar] = url
            return ""
        else:
            if context.autoescape:
                url = conditional_escape(url)
            return url


@register.tag
def reverse_app(parser, token):
    """
    Reverse app URLs, preferring the active language.

    Usage::

        {% load feincms3 %}
        {% reverse_app 'blog' 'detail' [args] [kw=args] [fallback='/'] %}

    ``namespaces`` can either be a list or a comma-separated list of
    namespaces. ``NoReverseMatch`` exceptions can be avoided by providing a
    ``fallback`` as a keyword argument or by saving the result in a variable,
    similar to ``{% url 'view' as url %}`` does::

        {% reverse_app 'newsletter' 'subscribe-form' fallback='/newsletter/' %}

    Or::

        {% reverse_app 'extranet' 'login' as login_url %}
    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(
            "'reverse_app' takes at least two arguments, a namespace and"
            " a URL pattern name."
        )
    namespaces = parser.compile_filter(bits[1])
    viewname = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None
    bits = bits[3:]
    if len(bits) >= 2 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to reverse_app tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return ReverseAppNode(namespaces, viewname, args, kwargs, asvar)
