from content_editor.models import Region, Template
from django.test.utils import isolate_apps

from feincms3.mixins import TemplateMixin


@isolate_apps("testapp")
def test_mixin():
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

    assert {region.key for region in Page(template_key="standard").regions} == {"main"}
    assert {region.key for region in Page(template_key="other").regions} == {
        "main",
        "other",
    }
    assert {region.key for region in Page(template_key="__notexists").regions} == {
        "main"
    }
