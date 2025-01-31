from contextlib import contextmanager

from django.urls import set_urlconf


@contextmanager
def override_urlconf(urlconf):
    set_urlconf(urlconf)
    try:
        yield
    finally:
        set_urlconf(None)
