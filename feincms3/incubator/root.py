"""
The guide recommends using a view for the feincms3 pages app. However, using
catch-all URLs together with ``i18n_patterns`` leads to the strange behavior
where 404-errors always lead to a redirect if the URL doesn't begin with a
language code, even for URLs where this isn't appropriate at all.

Using a middleware makes it possible to circumvent the necessity to add a
catch-all pattern to the URLconf. There's a downside to this though: We have to
hardcode the pages app mountpoint somewhere because it cannot be automatically
determined using ``reverse()`` and friends. This is the reason why this module
is called ``root``, because the page app's mountpoint has to be the Python
app's mountpoint when using this.

Example code for using this module (e.g. ``app.pages.middleware``):

.. code-block:: python

    from django.shortcuts import render
    from feincms3.incubator.root import add_redirect_handler, create_page_if_404_middleware

    from app.pages.models import Page
    from app.pages.utils import page_context

    # The page handler receives the request and the page.
    # ``add_redirect_handler`` wraps the handler function with support for the
    # RedirectMixin.
    handler = add_redirect_handler(
        lambda request, page: render(
            request, page.type.template_name, page_context(request, page=page)
        )
    )

    # This is the middleware which you want to add to ``MIDDLEWARE`` as
    # ``app.pages.middleware.page_if_404_middleware``. The middleware should be
    # added in the last position except if you have a very good reason not to
    # do this.
    page_if_404_middleware = create_page_if_404_middleware(
        queryset=Page.objects.active(),
        handler=handler,
    )
"""

from django.http import HttpResponseRedirect
from django.urls import get_script_prefix
from django.utils.encoding import iri_to_uri
from django.utils.text import slugify

from feincms3.pages import AbstractPage


class AbstractPage(AbstractPage):
    class Meta(AbstractPage.Meta):
        abstract = True

    def get_absolute_url(self):
        return iri_to_uri(get_script_prefix().rstrip("/") + self.path)


def create_page_if_404_middleware(*, queryset, handler, language_code_redirect=True):
    def outer(get_response):
        def inner(request):
            response = get_response(request)
            if response.status_code != 404:
                return response
            if page := queryset.filter(path=request.path_info).first():
                return handler(request, page)
            if language_code_redirect and request.path_info == "/":
                target = f"/{slugify(request.LANGUAGE_CODE)}/"
                if queryset.filter(path=target).exists():
                    return HttpResponseRedirect(target)
            return response

        return inner

    return outer


def add_redirect_handler(handler):
    def inner(request, page):
        if redirect_to := page.get_redirect_url():
            return HttpResponseRedirect(redirect_to)
        return handler(request, page)

    return inner
