from django import template
from django.conf import settings
from django.template.base import Node, TemplateSyntaxError, kwarg_re
from django.urls import NoReverseMatch
from django.utils.html import conditional_escape, mark_safe

from feincms3.applications import reverse_app as _reverse_app
from feincms3.utils import is_first_party_link


register = template.Library()


@register.simple_tag(takes_context=True)
def render_region(context, regions, region, **kwargs):
    """
    Render a single region. See :class:`~feincms3.renderer.RegionRenderer` for
    additional details.

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
        if not isinstance(namespaces, list | tuple):
            namespaces = namespaces.split(",")
        # Try to look up the URL. If it fails, raise NoReverseMatch unless the
        # {% reverse ... as var %} construct is used, in which case return
        # nothing.
        url = ""
        try:
            url = _reverse_app(
                namespaces,
                view_name,
                args=args,
                kwargs=kwargs,
                current_app=self._current_app(context),
            )
        except NoReverseMatch:
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


@register.filter
def translations(iterable, languages=None):
    """
    Return a list of dictionaries, one for each language in
    ``settings.LANGUAGES``. An example follows:

    .. code-block:: python

        [
            {"code": "en", "name": "English", "object": <instance>},
            {"code": "de", "name": "German", "object": None},
            # ...
        ]

    The filter accepts anything you throw at it. "It" should be an iterable of
    objects having a ``language_code`` property however, or anything
    non-iterable (such as ``None``). The filter always returns a list of all
    languages in ``settings.LANGUAGES`` but the ``object`` key's value will
    always be ``None`` if the data is unusable.
    """
    try:
        translations = {obj.language_code: obj for obj in iterable} if iterable else {}
    except TypeError:
        translations = {}

    return [
        {"code": code, "name": name, "object": translations.get(code)}
        for code, name in (languages or settings.LANGUAGES)
    ]


@register.simple_tag
def translations_from(*iterables, languages=None):
    t = {
        code: {"code": code, "name": name, "object": None}
        for code, name in (languages or settings.LANGUAGES)
    }
    for iterable in iterables:
        if iterable and not isinstance(iterable, str):
            for obj in iterable:
                t[obj.language_code]["object"] = obj
    return list(t.values())


@register.simple_tag
def maybe_target_blank(href, *, attributes='target="_blank" rel="noopener"'):
    """
    Return the value of ``attributes`` if the first argument isn't a first party link
    (as determined by :func:`~feincms3.utils.is_first_party_link`)

    Usage::

        <a href="{{ url }}" {% maybe_target_blank url %}>...</a>
    """
    if is_first_party_link(href):
        return ""
    return mark_safe(attributes)
