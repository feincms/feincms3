from collections import deque

from content_editor.contents import contents_for_item
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.test import TestCase
from django.utils.html import format_html, mark_safe

from feincms3.renderer import (
    PluginNotRegisteredError,
    RegionRenderer,
    template_renderer,
)
from testapp.models import HTML, Page, RichText


class RegionRendererTest(TestCase):
    def prepare(self):
        p = Page.objects.create(page_type="standard")

        RichText.objects.create(
            parent=p, region="main", ordering=10, text="<p>Hello</p>"
        )
        HTML.objects.create(parent=p, region="main", ordering=20, html="<br>")
        HTML.objects.create(parent=p, region="main", ordering=30, html="<hr>")
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
            '<div class="rt"><p>Hello</p></div> <br>x <hr>x <div class="rt"><p>World</p></div>',
        )

        RichText.objects.create(
            parent=p, region="main", ordering=40, text="<p>World</p>"
        )
        regions = renderer.regions_from_item(p, timeout=1)
        self.assertHTMLEqual(
            regions.render("main", Context({"outer": "x"})),
            '<div class="rt"><p>Hello</p></div> <br>x <hr>x <div class="rt"><p>World</p></div>',
        )

    def test_unconfigured_exception(self):
        renderer = RegionRenderer()
        contents = contents_for_item(self.prepare(), plugins=[RichText, HTML])
        regions = renderer.regions_from_contents(contents)
        with self.assertRaises(PluginNotRegisteredError):
            regions.render("main", None)
        with self.assertRaises(PluginNotRegisteredError):
            # All regions are rendered at once
            regions.render("does_not_exist", None)

    def test_subregions(self):
        class HTMLSubregionRenderer(RegionRenderer):
            def handle_html(self, plugins, context):
                return format_html(
                    '<div class="html">{}</div>',
                    mark_safe(
                        "".join(
                            self.render_plugin(plugin, context)
                            for plugin in self.takewhile_subregion(
                                plugins, subregion="html"
                            )
                        )
                    ),
                )

        renderer = HTMLSubregionRenderer()
        renderer.register(RichText, lambda plugin, context: mark_safe(plugin.text))
        renderer.register(
            HTML, lambda plugin, context: mark_safe(plugin.html), subregion="html"
        )

        regions = renderer.regions_from_item(self.prepare())
        self.assertHTMLEqual(
            regions.render("main", None),
            '<p>Hello</p> <div class="html"><br><hr></div> <p>World</p>',
        )

    def test_marks(self):
        class MarksRenderer(RegionRenderer):
            def render_region(self, *, region, contents, context):
                def _render():
                    plugins = deque(contents[region.key])
                    while plugins:
                        if items := list(self.takewhile_mark(plugins, mark="html")):
                            yield format_html(
                                '<div class="html">{}</div>',
                                mark_safe(
                                    "".join(
                                        self.render_plugin(plugin, context)
                                        for plugin in items
                                    )
                                ),
                            )
                        if items := list(self.takewhile_mark(plugins, mark="stuff")):
                            yield format_html(
                                '<div class="stuff">{}</div>',
                                mark_safe(
                                    "".join(
                                        self.render_plugin(plugin, context)
                                        for plugin in items
                                    )
                                ),
                            )

                return mark_safe("".join(output for output in _render()))

        renderer = MarksRenderer()
        renderer.register(
            RichText,
            lambda plugin, context: mark_safe(plugin.text),
            marks={"stuff"},
        )
        renderer.register(
            HTML,
            lambda plugin, context: mark_safe(plugin.html),
            marks=lambda plugin: {"html"},
        )

        regions = renderer.regions_from_item(self.prepare())
        self.assertHTMLEqual(
            regions.render("main", None),
            '<div class="stuff"><p>Hello</p></div><div class="html"><br><hr></div><div class="stuff"><p>World</p></div>',
        )

    def test_invalid_renderer(self):
        r = RegionRenderer()
        with self.assertRaisesRegex(
            ImproperlyConfigured, r"has less than the two required arguments"
        ):
            r.register(1, lambda plugin: "")

    def test_register_unregister(self):
        richtext_renderer = template_renderer("renderer/richtext.html")
        html_renderer = template_renderer("renderer/html.html")

        renderer = RegionRenderer()
        renderer.register(RichText, richtext_renderer)
        renderer.register(HTML, html_renderer)

        r2 = renderer.copy()
        r2.unregister(RichText)

        r3 = renderer.copy()
        r3.unregister(keep=[HTML])

        self.assertEqual(renderer._fetch, [RichText, HTML])
        self.assertEqual(
            renderer._renderers,
            {
                RichText: richtext_renderer,
                HTML: html_renderer,
            },
        )
        self.assertEqual(
            renderer._subregions,
            {RichText: "default", HTML: "default"},
        )
        self.assertEqual(
            renderer._subregions,
            {RichText: "default", HTML: "default"},
        )
        self.assertEqual(
            renderer._marks,
            {RichText: {"default"}, HTML: {"default"}},
        )

        self.assertEqual(
            r2._renderers,
            {
                HTML: html_renderer,
            },
        )
        self.assertEqual(
            r2._subregions,
            {HTML: "default"},
        )
        self.assertEqual(
            r2._subregions,
            {HTML: "default"},
        )
        self.assertEqual(
            r2._marks,
            {HTML: {"default"}},
        )

        self.assertEqual(
            r3._renderers,
            {
                HTML: html_renderer,
            },
        )
        self.assertEqual(
            r3._subregions,
            {HTML: "default"},
        )
        self.assertEqual(
            r3._subregions,
            {HTML: "default"},
        )
        self.assertEqual(
            r3._marks,
            {HTML: {"default"}},
        )

        with self.assertRaises(ImproperlyConfigured):
            renderer.unregister(HTML, keep=[RichText])
