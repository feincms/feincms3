"""
Page middleware (``feincms3.root.middleware``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The guide recommends using a middleware for the feincms3 pages app. This module
offers helpers and utilities to reduce the amount of code you have to write.
The reason why this module is called ``root`` is that the page app's mountpoint
has to be the Python app's mountpoint when using this. If that's not the case
you may want to write your own :ref:`urls-and-views`.

Example code for using this module (e.g. ``app.pages.middleware``):

.. code-block:: python

    from django.shortcuts import render
    from feincms3.root.middleware import add_redirect_handler, create_page_if_404_middleware

    from app.pages.models import Page
    from app.pages.utils import page_context

    # The page handler receives the request and the page.
    # ``add_redirect_handler`` wraps the handler function with support for the
    # RedirectMixin.
    @add_redirect_handler
    def handler(request, page):
        return render(request, page.type.template_name, page_context(request, page=page))

    # This is the middleware which you want to add to ``MIDDLEWARE`` as
    # ``app.pages.middleware.page_if_404_middleware``. The middleware should be
    # added in the last position except if you have a very good reason not to
    # do this.
    page_if_404_middleware = create_page_if_404_middleware(
        # queryset=Page.objects.active() works too (if .active() doesn't use
        # get_language or anything similar)
        queryset=lambda request: Page.objects.active(),

        handler=handler,
    )
"""

from functools import wraps

from django.conf import settings
from django.http import (
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)


class _UseRootMiddlewareResponse(HttpResponseNotFound):
    """Used by feincms3.root.passthru to tell the middleware to do its thing"""


def create_page_if_404_middleware(*, queryset, handler, language_code_redirect=False):
    """
    Create a middleware for handling pages

    This utility is there for your convenience, you do not have to use it. The
    returned middleware already handles returning non-404 responses as-is,
    fetching a page instance from the database and calling a user-defined
    handler on success. It optionally also supports redirecting requests to the
    root of the app to a language-specific landing page.

    Required arguments:

    - ``queryset``: A page queryset or a callable accepting the request and
      returning a page queryset.
    - ``handler``: A callable accepting the request and a page and returning a
      response.

    Optional arguments:

    - ``language_code_redirect`` (``False``): Redirect visitor to the language
      code prefix (e.g. ``/en/``, ``/de-ch/``) if request path equals the
      script prefix (generally ``/``) and no active page for ``/`` exists.
    """

    def outer(get_response):
        def inner(request):
            response = get_response(request)
            if response.status_code != 404 or (
                request.resolver_match
                and not isinstance(response, _UseRootMiddlewareResponse)
            ):
                # Response is not a 404 OR the 404 comes from a resolved view
                # which also didn't return a _UseRootMiddlewareResponse.
                return response
            qs = queryset(request) if callable(queryset) else queryset._clone()
            if page := qs.filter(path=request.path_info).first():
                return handler(request, page)
            if language_code_redirect and request.path_info == "/":
                target = f"/{request.LANGUAGE_CODE}/"
                if qs.filter(path=target).exists():
                    return HttpResponseRedirect(target)
            if settings.APPEND_SLASH and not request.path_info.endswith("/"):
                target = request.path_info + "/"
                if qs.filter(path=target).exists():
                    return HttpResponsePermanentRedirect(target)
            return response

        return inner

    return outer


def add_redirect_handler(handler):
    """
    Wrap the page handler in a redirect mixin handler
    """

    @wraps(handler)
    def inner(request, page):
        if redirect_to := page.get_redirect_url():
            return HttpResponseRedirect(redirect_to)
        return handler(request, page)

    return inner
