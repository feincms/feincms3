# from functools import lru_cache
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
