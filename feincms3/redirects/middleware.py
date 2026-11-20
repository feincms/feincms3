from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from feincms3.redirects.models import Redirect


def redirect_response(request):
    """
    Return a redirect response for the request if a matching redirect exists,
    ``None`` otherwise
    """
    if "\x00" in request.path:
        return None
    if found := Redirect.objects.find(request):
        url, permanent = found
        cls = HttpResponsePermanentRedirect if permanent else HttpResponseRedirect
        return cls(url)
    return None


def redirects_middleware(get_response):
    """
    Redirect requests resulting in a 404 response if a redirect matches

    Add the middleware *before* middleware which may handle 404 responses
    itself, e.g. the page middleware created by
    :func:`feincms3.root.middleware.create_page_if_404_middleware`, so that
    those have a chance to handle the request first.
    """

    def middleware(request):
        response = get_response(request)
        if response.status_code == 404 and (redirect := redirect_response(request)):
            return redirect
        return response

    return middleware
