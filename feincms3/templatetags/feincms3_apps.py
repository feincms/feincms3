import warnings

from django import template

from feincms3.templatetags.feincms3 import reverse_app as _reverse_app


register = template.Library()


@register.tag
def reverse_app(parser, token):
    warnings.warn(
        "Load reverse_app using {% load feincms3 %} instead."
        " The feincms3_apps template tag library has been deprecated and"
        " will be removed soon.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _reverse_app(parser, token)
