from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import include, path, re_path
from testapp import views


pages_urlpatterns = (
    [
        path("", lambda request: HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)),
        re_path(r"^(?P<path>[-\w/]+)/$", views.page_detail, name="page"),
        path("", views.page_detail, name="root"),
    ],
    "pages",
)


urlpatterns = i18n_patterns(
    path("i18n/", lambda request: HttpResponse(request.LANGUAGE_CODE))
) + [
    path("admin/", admin.site.urls),
    path("404/", lambda request: render(request, "404.html")),
    path("", include(pages_urlpatterns)),
]
