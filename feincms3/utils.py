from django.core.exceptions import ValidationError
from django.utils.lru_cache import lru_cache


def iterate_subclasses(cls):
    """
    Yields the passed class and all its subclasses in depth-first order.
    """

    for scls in cls.__subclasses__():
        yield scls
        yield from iterate_subclasses(scls)


@lru_cache(maxsize=None)
def concrete_model(abstract):
    """
    Returns the first concrete model found when iterating subclasses in a
    depth-first fashion.
    """
    for cls in iterate_subclasses(abstract):
        if not cls._meta.abstract:
            return cls


def validation_error(error, *, field, exclude, **kwargs):
    """
    Return a validation error that is associated with a particular field if it
    isn't excluded from validation.

    See https://github.com/django/django/commit/e8c056c31 for some background.
    """
    return ValidationError(
        error if field in (exclude or ()) else {field: error}, **kwargs
    )
