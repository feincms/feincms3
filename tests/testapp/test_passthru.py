from contextlib import contextmanager

import pytest
from django.urls import NoReverseMatch, set_urlconf
from pytest_django.asserts import assertContains

from feincms3.applications import apps_urlconf
from feincms3.root.passthru import reverse_passthru, reverse_passthru_lazy
from testapp.models import Page


@contextmanager
def override_urlconf(urlconf):
    set_urlconf(urlconf)
    try:
        yield
    finally:
        set_urlconf(None)


@pytest.mark.django_db
def test_passthru_render(client):
    """The passthru view returns a HttpResponseNotFound but the middleware renders a thing"""
    Page.objects.create(
        title="Impressum",
        slug="impressum",
        path="/de/impressum/",
        static_path=True,
        language_code="de",
        is_active=True,
        page_type="imprint",
    )

    response = client.get("/de/impressum/")
    assertContains(response, "<h1>Impressum</h1>")
    # print(response, response.content.decode("utf-8"))

    # No catch-all; subpages produce a proper 404 ...
    response = client.get("/de/impressum/not-yet/")
    assert response.status_code == 404

    Page.objects.create(
        title="not-yet",
        slug="not-yet",
        path="/de/impressum/not-yet/",
        static_path=True,
        language_code="de",
        is_active=True,
    )

    # ... but once the subpage actually exists it is found and rendered
    response = client.get("/de/impressum/not-yet/")
    assertContains(response, "<h1>not-yet</h1>")


@pytest.mark.django_db
def test_reverse_passthru():
    """Try reversing passthru views"""
    lazy = reverse_passthru_lazy("imprint")

    Page.objects.create(
        title="Impressum",
        slug="impressum",
        path="/de/impressum/",
        static_path=True,
        language_code="de",
        is_active=True,
        page_type="imprint",
    )

    with pytest.raises(NoReverseMatch):
        reverse_passthru("imprint")
    with pytest.raises(NoReverseMatch):
        str(lazy)
    with override_urlconf(apps_urlconf()):
        url = reverse_passthru("imprint")
        assert url == "/de/impressum/"
        assert str(lazy) == "/de/impressum/"

    # The fallback keyword argument is supported
    assert reverse_passthru("imprint", fallback="/asdf/") == "/asdf/"

    # Outside the request-response cycle
    url = reverse_passthru("imprint", urlconf=apps_urlconf())
    assert url == "/de/impressum/"

    # Only this language
    with pytest.raises(NoReverseMatch):
        reverse_passthru("imprint", urlconf=apps_urlconf(), languages=["en"])
