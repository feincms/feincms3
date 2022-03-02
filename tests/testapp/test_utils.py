from django.template import Context, Template
from django.test import TestCase
from django.test.utils import override_settings

from feincms3.utils import is_first_party_link


class Test(TestCase):
    def test_is_first_party_link(self):
        """is_first_party_link test battery"""

        TESTS = [
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
        ]

        for url, hosts, result in TESTS:
            with self.subTest(url=url, hosts=hosts, result=result):
                self.assertEqual(
                    is_first_party_link(url, first_party_hosts=hosts), result
                )

    @override_settings(ALLOWED_HOSTS=[".example.com"])
    def test_href_template_tag(self):
        template = Template(
            "{% load feincms3 %}<a {{ url|href_maybe_target_blank }}>link</a>"
        )

        html = template.render(Context({"url": "/relative/"}))
        self.assertEqual(
            html,
            '<a href="/relative/">link</a>',
        )

        html = template.render(Context({"url": "http://example.org/relative/"}))
        self.assertEqual(
            html,
            '<a href="http://example.org/relative/" target="_blank" rel="noopener">link</a>',
        )
