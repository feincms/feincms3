from content_editor.models import Region, Template
from django.test import TestCase
from django.test.utils import isolate_apps

from feincms3.mixins import TemplateMixin


class TemplateMixinTest(TestCase):
    @isolate_apps("testapp")
    def test_mixin(self):
        class Page(TemplateMixin):
            TEMPLATES = [
                Template(
                    key="standard",
                    title="standard",
                    template_name="pages/standard.html",
                    regions=[
                        Region(key="main", title="main"),
                    ],
                ),
                Template(
                    key="other",
                    title="other",
                    template_name="pages/other.html",
                    regions=[
                        Region(key="main", title="main"),
                        Region(key="other", title="other"),
                    ],
                ),
            ]

        self.assertEqual(
            {region.key for region in Page(template_key="standard").regions},
            {"main"},
        )
        self.assertEqual(
            {region.key for region in Page(template_key="other").regions},
            {"main", "other"},
        )
        self.assertEqual(
            {region.key for region in Page(template_key="__notexists").regions},
            {"main"},
        )
