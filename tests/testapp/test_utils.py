import datetime as dt
from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.test.utils import override_settings
from pytest_django.asserts import assertHTMLEqual

from feincms3.utils import is_first_party_link, upload_to


@pytest.mark.parametrize(
    "url, hosts, result",
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
