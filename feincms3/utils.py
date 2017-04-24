from functools import wraps

from django.utils.lru_cache import lru_cache


def _iterate_subclasses(cls):
    """
    Yields the passed class and all its subclasses in depth-first order.
    """

    for scls in cls.__subclasses__():
        yield scls
        # yield from _iterate_subclasses(scls)
        for c in _iterate_subclasses(scls):
            yield c


@lru_cache(maxsize=8)
def concrete_model(abstract):
    for cls in _iterate_subclasses(abstract):
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
                    'Only %s positional arguments allowed' % count)
            return fn(*args, **kwargs)
        return _fn
    return _dec
