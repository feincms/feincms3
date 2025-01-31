import datetime as dt
from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.test.utils import override_settings
from pytest_django.asserts import assertHTMLEqual

from feincms3.shortcuts import render_list
from feincms3.utils import is_first_party_link, upload_to
from testapp.models import Article


@pytest.mark.parametrize(
    ("url", "hosts", "result"),
    [
        (
            "http://example.com/",
            ["*"],
            False,
        ),
        (
            "http://example.com:80/path",
            [".example.com"],
            True,
        ),
        (
            "https://example.com:80/path",
            [".example.com"],
            True,
        ),
        (
            "http://www.example.com:80/path",
            ["example.com"],
            False,
        ),
        (
            "/path",
            [".example.com"],
            True,
        ),
        (
            "mailto:max@example.com",
            [".example.com"],
            False,
        ),
        (
            "ftp://example.com:80/path",
            [".example.com"],
            False,
        ),
    ],
)
def test_is_first_party_link(url, hosts, result):
    """is_first_party_link test battery"""
    assert is_first_party_link(url, first_party_hosts=hosts) == result


@override_settings(ALLOWED_HOSTS=[".example.com"])
def test_maybe_target_blank_template_tag():
    template = Template(
        '{% load feincms3 %}<a href="{{ url }}" {% maybe_target_blank url %}>link</a>'
    )

    html = template.render(Context({"url": "/relative/"}))
    assertHTMLEqual(
        html,
        '<a href="/relative/">link</a>',
    )

    html = template.render(Context({"url": "http://example.org/relative/"}))
    assertHTMLEqual(
        html,
        '<a href="http://example.org/relative/" target="_blank" rel="noopener">link</a>',
    )


def test_upload_to():
    instance = SimpleNamespace(_meta=SimpleNamespace(model_name="image"))
    ordinal = str(dt.date.today().toordinal())
    filename = "upload.jpg"

    assert upload_to(instance, filename) == "/".join(
        ["image", ordinal[1:3], ordinal[3:6], filename]
    )


@pytest.mark.django_db
def test_render_list():
    """render_list, automatic template selection and pagination"""
    for i in range(7):
        Article.objects.create(title=f"Article {i}", category="publications")

    request = RequestFactory().get("/", data={"page": 2})
    response = render_list(
        request, list(Article.objects.all()), model=Article, paginate_by=2
    )

    assert response.template_name == "testapp/article_list.html"
    assert len(response.context_data["object_list"]) == 2
    assert response.context_data["object_list"].number == 2
    assert response.context_data["object_list"].paginator.num_pages == 4
