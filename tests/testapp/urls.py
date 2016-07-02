from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponseRedirect

from testapp import views


pages_urlpatterns = ([
    url(
        r'^$',
        lambda request: HttpResponseRedirect('/%s/' % request.LANGUAGE_CODE),
    ),
    url(
        r'^(?P<path>[-\w/]+)/$',
        views.page_detail,
        name='page',
    ),
    url(
        r'^$',
        views.page_detail,
        name='root',
    ),
], 'pages')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include(pages_urlpatterns)),
]
