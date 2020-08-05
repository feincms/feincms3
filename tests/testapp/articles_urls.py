from django.shortcuts import get_object_or_404
from django.urls import path

from feincms3.applications import page_for_app_request
from feincms3.shortcuts import render_detail, render_list

from .models import Article


def article_list_all(request):
    page = page_for_app_request(request)
    page.activate_language(request)
    return render_list(
        request, Article.objects.filter(category=page.application), {"page": page}
    )


def article_list(request):
    page = page_for_app_request(request)
    page.activate_language(request)
    return render_list(
        request,
        Article.objects.filter(category=page.application),
        {"page": page},
        paginate_by=5,
    )


def article_detail(request, pk):
    page = page_for_app_request(request)
    page.activate_language(request)
    return render_detail(request, get_object_or_404(Article, pk=pk), {"page": page})


app_name = "articles"
urlpatterns = [
    path("all/", article_list_all, name="article-list-all"),
    path("", article_list, name="article-list"),
    path("<int:pk>/", article_detail, name="article-detail"),
]
