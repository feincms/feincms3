"""
Passthru page apps (``feincms3.root.passthru``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The idea of this module is to allow tagging pages to allow programmatically
determing the URL of pages which are often linked to, e.g. privacy policy or
imprint pages.

Create an application type:

.. code-block:: python

    TYPES = [
        ...
        ApplicationType(
            key="imprint",
            title=_("imprint"),
            urlconf="feincms3.root.passthru",
            template_name="pages/standard.html",
            regions=[Region(key="main", title=_("Main"))],
        ),
    ]

Reverse the URL of the page (if it exists):

.. code-block:: python

    # Raise NoReverseMatch on failure
    reverse_passthru("imprint")

    # Fallback
    reverse_passthru("imprint", fallback="/en/imprint/")

    # Outside the request-response cycle
    reverse_passthru("imprint", urlconf=apps_urlconf())
"""

from functools import partial

from django.urls import path
from django.utils.functional import lazy

from feincms3.applications import reverse_app
from feincms3.root.middleware import _UseRootMiddlewareResponse


app_name = "passthru"
urlpatterns = [path("", lambda request: _UseRootMiddlewareResponse(), name="passthru")]
ignore_app_name_mismatch = True


def reverse_passthru(namespace, **kwargs):
    """
    Reverse a passthru app URL

    Raises ``NoReverseMatch`` if page could not be found.
    """
    return reverse_app(namespace, "passthru", **kwargs)


def reverse_passthru_lazy(namespace, **kwargs):
    return lazy(partial(reverse_passthru, namespace, **kwargs), str)()
