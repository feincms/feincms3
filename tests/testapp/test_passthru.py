from contextlib import contextmanager

from django.test import TestCase
from django.urls import NoReverseMatch, set_urlconf

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


class Test(TestCase):
    def test_passthru_render(self):
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

        response = self.client.get("/de/impressum/")
        self.assertContains(response, "<h1>Impressum</h1>")
        # print(response, response.content.decode("utf-8"))

        # No catch-all; subpages produce a proper 404 ...
        response = self.client.get("/de/impressum/not-yet/")
        self.assertEqual(response.status_code, 404)

        Page.objects.create(
            title="not-yet",
            slug="not-yet",
            path="/de/impressum/not-yet/",
            static_path=True,
            language_code="de",
            is_active=True,
        )

        # ... but once the subpage actually exists it is found and rendered
        response = self.client.get("/de/impressum/not-yet/")
        self.assertContains(response, "<h1>not-yet</h1>")

    def test_reverse_passthru(self):
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

        with self.assertRaises(NoReverseMatch):
            reverse_passthru("imprint")
        with self.assertRaises(NoReverseMatch):
            str(lazy)
        with override_urlconf(apps_urlconf()):
            url = reverse_passthru("imprint")
            self.assertEqual(url, "/de/impressum/")
            self.assertEqual(str(lazy), "/de/impressum/")

        # The fallback keyword argument is supported
        self.assertEqual(reverse_passthru("imprint", fallback="/asdf/"), "/asdf/")

        # Outside the request-response cycle
        url = reverse_passthru("imprint", urlconf=apps_urlconf())
        self.assertEqual(url, "/de/impressum/")

        # Only this language
        with self.assertRaises(NoReverseMatch):
            reverse_passthru("imprint", urlconf=apps_urlconf(), languages=["en"])
