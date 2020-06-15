from django.conf.urls import url
from django.shortcuts import get_object_or_404

from feincms3.apps import page_for_app_request
from feincms3.shortcuts import render_detail

from .models import TranslatedArticle


def detail(request, pk):
    page = page_for_app_request(request)
    page.activate_language(request)
    return render_detail(
        request, get_object_or_404(TranslatedArticle, pk=pk), {"page": page}
    )


app_name = "translated-articles"
urlpatterns = [url(r"^(?P<pk>[0-9]+)/$", detail, name="detail")]
