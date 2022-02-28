from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path


urlpatterns = i18n_patterns(
    path("i18n/", lambda request: HttpResponse(request.LANGUAGE_CODE))
) + [
    path("admin/", admin.site.urls),
    path("404/", lambda request: render(request, "404.html")),
]
