import datetime as dt
import posixpath
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.http import is_same_domain


def validation_error(error, *, field, exclude, **kwargs):
    """
    Return a validation error that is associated with a particular field if it
    isn't excluded from validation.

    See https://github.com/django/django/commit/e8c056c31 for some background.
    """
    return ValidationError(
        error if field in (exclude or ()) else {field: error}, **kwargs
    )


def is_first_party_link(url, *, first_party_hosts=None):
    """
    Return whether an URL is a first-party link or not.

    First parties are defined by ``ALLOWED_HOSTS`` and can be overridden by
    passing an alternative list of hosts. The wildcard ``["*"]`` isn't
    recognized.

    NOTE! ``first_party_hosts`` should not contain port numbers even if using a
    non-standard port, the same is true for Django's ``ALLOWED_HOSTS`` setting.

    One template tag is available to help with ensuring off-site links open in
    a new window (if you need this...). The template tag does not allow
    specifying the list of first party hosts (it always uses
    ``ALLOWED_HOSTS``):

    .. code-block:: html+django

        {% load feincms3 %}
        <a href="{{ url }}" {% maybe_target_blank url %}>text</a>
    """
    u = urlparse(url)

    if u.scheme and u.scheme not in {"http", "https"}:
        return False

    if not u.hostname:
        return True

    hosts = settings.ALLOWED_HOSTS if first_party_hosts is None else first_party_hosts
    return any(is_same_domain(u.hostname, pattern) for pattern in hosts)


class ChoicesCharField(models.CharField):
    """
    ``models.CharField`` with choices, which makes the migration framework
    always ignore changes to ``choices``, ever.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", [("", "")])  # Non-empty choices for get_*_display
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["choices"] = [("", "")]
        return name, "django.db.models.CharField", args, kwargs


def upload_to(instance, filename):
    """
    Standard ``upload_to`` callable for feincms3 file fields

    The generated path consists of:

    - The instance's lowercased model label
    - A part of the proleptic Gregorian ordinal of the date
    - The original filename

    The ordinal changes each day which means that filename collisions only
    happen when uploading to the same model (or one with the same name in a
    different app) and on the same day. This is much better than the previous
    default of using ``images/%Y/%m`` where you had to wait up to a full month
    to avoid collisions.
    """

    ordinal = str(dt.date.today().toordinal())
    return posixpath.join(
        instance._meta.model_name,
        ordinal[1:3],  # cut the first digit, it will only reach 800000 in 2191.
        ordinal[3:],
        filename,
    )
