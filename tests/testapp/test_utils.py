from django.test import TestCase

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
