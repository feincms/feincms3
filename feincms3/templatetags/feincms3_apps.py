import warnings

from django import template

from feincms3.templatetags.feincms3 import reverse_app


warnings.warn(
    "Load reverse_app using {% load feincms3 %} instead."
    " The feincms3_apps template tag library has been deprecated and"
    " will be removed soon.",
    Warning,
)


register = template.Library()
register.tag(reverse_app)
