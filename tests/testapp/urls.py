from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import path


def not_found(request):
    raise Http404


def handler404(request, exception):
    return HttpResponse("My not found handler", status=404)


urlpatterns = i18n_patterns(
    path("i18n/", lambda request: HttpResponse(request.LANGUAGE_CODE))
) + [
    path("admin/", admin.site.urls),
    path("not-found/", not_found),
]
