""""
NOTE! Please do not depend upon any utilities in this file. Utilities are
added, modified and dropped without prior notice. This file is only for
feincms3's internal use.

Of course you may always copy the code somewhere else if you like it
(according to the very permissive license of course).
"""

from functools import wraps

from django.core.exceptions import ValidationError
from django.utils.lru_cache import lru_cache


def iterate_subclasses(cls):
    """
    Yields the passed class and all its subclasses in depth-first order.
    """

    for scls in cls.__subclasses__():
        yield scls
        # yield from iterate_subclasses(scls)
        for c in iterate_subclasses(scls):
            yield c


@lru_cache(maxsize=None)
def concrete_model(abstract):
    for cls in iterate_subclasses(abstract):
        if not cls._meta.abstract:
            return cls


def positional(count):
    """
    Only allows ``count`` positional arguments to the decorated callable

    Will be removed as soon as we drop support for Python 2.
    """

    def _dec(fn):
        @wraps(fn)
        def _fn(*args, **kwargs):
            if len(args) > count:
                raise TypeError(
                    "Only %s positional argument%s allowed"
                    % (count, "" if count == 1 else "s")
                )
            return fn(*args, **kwargs)

        return _fn

    return _dec


@positional(1)
def validation_error(error, field, exclude, **kwargs):
    """
    Return a validation error that is associated with a particular field if it
    isn't excluded from validation.

    See https://github.com/django/django/commit/e8c056c31 for some background.
    """
    return ValidationError(
        error if field in (exclude or ()) else {field: error}, **kwargs
    )
