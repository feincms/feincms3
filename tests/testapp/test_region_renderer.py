from content_editor.contents import contents_for_item
from django.template import Context
from django.test import TestCase
from django.utils.html import format_html, mark_safe
from testapp.models import HTML, Page, RichText

from feincms3.renderer import PluginNotRegistered, RegionRenderer, template_renderer


class RegionRendererTest(TestCase):
    def prepare(self):
        p = Page.objects.create(page_type="standard")

        RichText.objects.create(
            parent=p, region="main", ordering=10, text="<p>Hello</p>"
        )
        HTML.objects.create(parent=p, region="main", ordering=20, html="<a>")
        HTML.objects.create(parent=p, region="main", ordering=30, html="<b>")
        RichText.objects.create(
            parent=p, region="main", ordering=40, text="<p>World</p>"
        )

        return p

    def test_basic_rendering(self):
        p = self.prepare()

        renderer = RegionRenderer()
        renderer.register(
            RichText,
            template_renderer("renderer/richtext.html"),
        )
        renderer.register(
            HTML,
            template_renderer("renderer/html.html"),
        )

        regions = renderer.regions_from_item(p, timeout=1)
        self.assertHTMLEqual(
            regions.render("main", Context({"outer": "x"})),
            '<div class="rt"><p>Hello</p></div> <a>x <b>x <div class="rt"><p>World</p></div>',
        )

        RichText.objects.create(
            parent=p, region="main", ordering=40, text="<p>World</p>"
        )
        regions = renderer.regions_from_item(p, timeout=1)
        self.assertHTMLEqual(
            regions.render("main", Context({"outer": "x"})),
            '<div class="rt"><p>Hello</p></div> <a>x <b>x <div class="rt"><p>World</p></div>',
        )

    def test_unconfigured_exception(self):
        renderer = RegionRenderer()
        contents = contents_for_item(self.prepare(), plugins=[RichText, HTML])
        regions = renderer.regions_from_contents(contents)
        with self.assertRaises(PluginNotRegistered):
            regions.render("main", None)
        with self.assertRaises(PluginNotRegistered):
            # All regions are rendered at once
            regions.render("does_not_exist", None)

    def test_subregions(self):
        class HTMLSubregionRenderer(RegionRenderer):
            def handle_html(self, items, context):
                return format_html(
                    '<div class="html">{}</div>',
                    mark_safe(
                        "".join(
                            self.render_item(item, context)
                            for item in self.takewhile(items, subregion="html")
                        )
                    ),
                )

        renderer = HTMLSubregionRenderer()
        renderer.register(RichText, lambda item, context: mark_safe(item.text))
        renderer.register(
            HTML, lambda item, context: mark_safe(item.html), subregion="html"
        )

        regions = renderer.regions_from_item(self.prepare())
        self.assertHTMLEqual(
            regions.render("main", None),
            '<p>Hello</p> <div class="html"><a><b></div> <p>World</p>',
        )
