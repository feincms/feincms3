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
        if not isinstance(namespaces, (list, tuple)):
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
    args, kwargs, asvar = _parse_reverse_bits(parser, bits[3:], "reverse_app")
    return ReverseAppNode(namespaces, viewname, args, kwargs, asvar)


@register.tag
def reverse_passthru(parser, token):
    """
    Reverse a passthru app URL, preferring the active language.

    Usage::

        {% load feincms3 %}
        {% reverse_passthru 'imprint' [fallback='/'] %}

    This is the template tag version of
    :func:`~feincms3.root.passthru.reverse_passthru`. It saves you from having
    to know that the view inside the passthru URLconf is called ``passthru``;
    the tag above is exactly equivalent to::

        {% reverse_app 'imprint' 'passthru' %}

    Passthru pages may simply not have been created yet, which makes the
    ``{% ... as var %}`` form -- it assigns an empty string instead of raising
    ``NoReverseMatch`` -- the most useful one here::

        {% reverse_passthru 'imprint' as imprint_url %}
        {% if imprint_url %}<a href="{{ imprint_url }}">{% translate "Imprint" %}</a>{% endif %}

    A ``fallback`` keyword argument is supported as well.
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "'reverse_passthru' takes at least one argument, a namespace."
        )
    namespaces = parser.compile_filter(bits[1])
    args, kwargs, asvar = _parse_reverse_bits(parser, bits[2:], "reverse_passthru")
    if args:
        raise TemplateSyntaxError(
            "'reverse_passthru' doesn't support positional arguments; the"
            " passthru view doesn't take any."
        )
    return ReverseAppNode(
        namespaces, parser.compile_filter("'passthru'"), args, kwargs, asvar
    )


def _parse_reverse_bits(parser, bits, tag_name):
    args = []
    kwargs = {}
    asvar = None
    if len(bits) >= 2 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]

    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError(f"Malformed arguments to {tag_name} tag")
        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)
        else:
            args.append(parser.compile_filter(value))

    return args, kwargs, asvar


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
    """
    Return a list of dictionaries, one for each language in
    ``settings.LANGUAGES``, built from several sources of translations.

    This is the counterpart to the :func:`~feincms3.templatetags.feincms3.translations`
    filter for the case where more than one object may provide the translation
    for a given language. The iterables are applied in order and later ones win,
    so the most specific source goes last:

    .. code-block:: html+django

        {% load feincms3 %}
        {% translations_from page.translations.active article.translations.active as languages %}
        <nav class="languages">
          {% for lang in languages %}
            <a href="{% if lang.object %}{{ lang.object.get_absolute_url }}{% else %}/{{ lang.code }}/{% endif %}">
              {{ lang.name }}
            </a>
          {% endfor %}
        </nav>

    The menu above links the translated article where one exists and falls back
    to the translated page everywhere else. The return value has the same shape
    as the one from :func:`~feincms3.templatetags.feincms3.translations`:

    .. code-block:: python

        [
            {"code": "en", "name": "English", "object": <instance>},
            {"code": "de", "name": "German", "object": None},
            # ...
        ]

    Arguments which are falsy or which are strings are skipped, and objects
    whose ``language_code`` isn't in the list of languages are ignored, so
    neither optional objects nor rows in a language which has since been
    removed from the setting have to be guarded against at the call site. Pass a
    ``languages`` keyword argument containing a list of ``(code, name)`` tuples
    to override the set of languages.
    """
    t = {
        code: {"code": code, "name": name, "object": None}
        for code, name in (languages or settings.LANGUAGES)
    }
    for iterable in iterables:
        if iterable and not isinstance(iterable, str):
            for obj in iterable:
                if entry := t.get(obj.language_code):
                    entry["object"] = obj
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
