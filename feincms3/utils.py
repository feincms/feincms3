from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
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
    Verify whether an URL is a first-party link or not.

    First parties are defined by ``ALLOWED_HOSTS`` and can be overridden by
    passing an alternative list of hosts. The wildcard ``["*"]`` isn't
    recognized.
    """
    u = urlparse(url)

    if u.scheme and u.scheme not in {"http", "https"}:
        return False

    if not u.hostname:
        return True

    hosts = settings.ALLOWED_HOSTS if first_party_hosts is None else first_party_hosts
    return any(is_same_domain(u.hostname, pattern) for pattern in hosts)
