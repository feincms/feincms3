from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from testapp import views


pages_urlpatterns = (
    [
        url(
            r"^$",
            lambda request: HttpResponseRedirect(
                "/%s/" % request.LANGUAGE_CODE
            ),
        ),
        url(r"^(?P<path>[-\w/]+)/$", views.page_detail, name="page"),
        url(r"^$", views.page_detail, name="root"),
    ],
    "pages",
)


urlpatterns = i18n_patterns(
    url(r"^i18n/$", lambda request: HttpResponse(request.LANGUAGE_CODE))
) + [
    url(r"^admin/", admin.site.urls),
    url(r"^404/$", lambda request: render(request, "404.html")),
    url(r"", include(pages_urlpatterns)),
]
