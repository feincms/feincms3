from collections import deque

import pytest
from content_editor.contents import contents_for_item
from content_editor.models import Region
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.utils.html import format_html, mark_safe
from pytest_django.asserts import assertHTMLEqual

from feincms3.renderer import (
    CLOSE_SECTION,
    PluginNotRegisteredError,
    RegionRenderer,
    template_renderer,
)
from testapp.models import HTML, Page, RichText


@pytest.fixture
def prepare():
    p = Page.objects.create(page_type="standard")

    RichText.objects.create(parent=p, region="main", ordering=10, text="<p>Hello</p>")
    HTML.objects.create(parent=p, region="main", ordering=20, html="<br>")
    HTML.objects.create(parent=p, region="main", ordering=30, html="<hr>")
    RichText.objects.create(parent=p, region="main", ordering=40, text="<p>World</p>")

    return p


@pytest.mark.django_db
def test_basic_rendering(prepare):
    p = prepare

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
    assertHTMLEqual(
        regions.render("main", Context({"outer": "x"})),
        '<div class="rt"><p>Hello</p></div> <br>x <hr>x <div class="rt"><p>World</p></div>',
    )

    RichText.objects.create(parent=p, region="main", ordering=40, text="<p>World</p>")
    regions = renderer.regions_from_item(p, timeout=1)
    assertHTMLEqual(
        regions.render("main", Context({"outer": "x"})),
        '<div class="rt"><p>Hello</p></div> <br>x <hr>x <div class="rt"><p>World</p></div>',
    )


@pytest.mark.django_db
def test_unconfigured_exception(prepare):
    renderer = RegionRenderer()
    contents = contents_for_item(prepare, plugins=[RichText, HTML])
    regions = renderer.regions_from_contents(contents)
    with pytest.raises(PluginNotRegisteredError):
        regions.render("main", None)
    with pytest.raises(PluginNotRegisteredError):
        # All regions are rendered at once
        regions.render("does_not_exist", None)


@pytest.mark.django_db
def test_subregions(prepare):
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

    regions = renderer.regions_from_item(prepare)
    assertHTMLEqual(
        regions.render("main", None),
        '<p>Hello</p> <div class="html"><br><hr></div> <p>World</p>',
    )


@pytest.mark.django_db
def test_marks(prepare):
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

    regions = renderer.regions_from_item(prepare)
    assertHTMLEqual(
        regions.render("main", None),
        '<div class="stuff"><p>Hello</p></div><div class="html"><br><hr></div><div class="stuff"><p>World</p></div>',
    )


def test_invalid_renderer():
    r = RegionRenderer()
    with pytest.raises(
        ImproperlyConfigured, match=r"has less than the two required arguments"
    ):
        r.register(1, lambda plugin: "")


def test_fetch():
    renderer = RegionRenderer()
    renderer.register(
        RichText,
        template_renderer("renderer/richtext.html"),
    )
    renderer.register(
        HTML,
        template_renderer("renderer/html.html"),
        fetch=False,
    )

    assert renderer.plugins() == [RichText]
    assert renderer.plugins(fetch=False) == [RichText, HTML]


def test_register_unregister():
    richtext_renderer = template_renderer("renderer/richtext.html")
    html_renderer = template_renderer("renderer/html.html")

    richtext_cfg = (RichText, richtext_renderer, "default", {"default"}, True)
    html_cfg = (HTML, html_renderer, "default", {"default"}, True)

    renderer = RegionRenderer()
    renderer.register(RichText, richtext_renderer)
    renderer.register(HTML, html_renderer)

    r2 = renderer.copy()
    r2.unregister(RichText)

    r3 = renderer.copy()
    r3.unregister(keep=[HTML])

    assert renderer._plugins == {RichText: richtext_cfg, HTML: html_cfg}
    assert r2._plugins == {HTML: html_cfg}
    assert r3._plugins == {HTML: html_cfg}

    with pytest.raises(ImproperlyConfigured):
        renderer.unregister(HTML, keep=[RichText])
    with pytest.raises(ImproperlyConfigured):
        renderer.unregister()


def test_sections():
    class SectionRenderer(RegionRenderer):
        def handle_images(self, plugins, context):
            content = "".join(
                self.render_plugin(p, context)
                for p in self.takewhile_subregion(plugins, "images")
            )
            yield f"<gallery>{content}</gallery>"

        def handle_section(self, plugins, context):
            section = plugins.popleft()
            content = self.render_section_plugins(section, plugins, context)
            return f"<section>{''.join(content)}</section>"

    class Text:
        pass

    class Image:
        pass

    class Section:
        pass

    class CloseSection:
        pass

    renderer = SectionRenderer()
    renderer.register(Text, "Text")
    renderer.register(Image, "Image", subregion="images")
    renderer.register(Section, "", subregion="section")
    renderer.register(CloseSection, "", subregion=CLOSE_SECTION)

    def render(plugins):
        return renderer.render_region(
            region=Region(key="content", title="Content"),
            contents={"content": plugins},
            context=None,
        )

    t = Text()
    i = Image()
    s = Section()
    c = CloseSection()

    # Basic tests
    assert render([t, t]) == "TextText"
    assert render([t, t, i, i, t]) == "TextText<gallery>ImageImage</gallery>Text"

    # Automatic closing of sections
    assert render([s, t]) == "<section>Text</section>"

    # Superfluous CloseSection objects are ignored
    assert render([s, t, c, c]) == "<section>Text</section>"

    # Nested sections, the images subregion is also rendered within the outer section
    assert (
        render([t, s, t, s, t, c, i])
        == "Text<section>Text<section>Text</section><gallery>Image</gallery></section>"
    )

    # The images subregion doesn't support nested sections and is automatically closed
    assert (
        render([t, i, i, s, t])
        == "Text<gallery>ImageImage</gallery><section>Text</section>"
    )
