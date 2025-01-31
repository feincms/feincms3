from types import SimpleNamespace

import pytest
from django.template import Context, Template

from feincms3.regions import Regions, matches
from feincms3.renderer import TemplatePluginRenderer
from testapp.models import HTML, Page


class Text(SimpleNamespace):
    pass


class Teaser(SimpleNamespace):
    subregion = "teasers"


class FAQ(SimpleNamespace):
    subregion = "faq"


class Command(SimpleNamespace):
    subregion = ""


class File(SimpleNamespace):
    pass


@pytest.fixture
def renderer():
    renderer = TemplatePluginRenderer()
    renderer.register_string_renderer(Text, lambda plugin: plugin.text)
    renderer.register_string_renderer(Teaser, lambda plugin: plugin.text)
    renderer.register_string_renderer(FAQ, lambda plugin: plugin.text)
    renderer.register_string_renderer(File, lambda plugin: plugin.text)
    renderer.register_string_renderer(Command, "")
    return renderer


class MyRegions(Regions):
    def handle_teasers(self, items, context):
        yield '<div class="teasers">'
        while True:
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
            if not items or not matches(items[0], plugins=(Teaser,)):
                break
        yield "</div>"

    def handle_faq(self, items, context):
        yield '<div class="faq">'
        while True:
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
            if not items or not matches(
                items[0], plugins=(FAQ, File), subregions={None, "faq"}
            ):
                break
        yield "</div>"


def test_enter_exit(renderer):
    """Entering and exiting the teasers subregion produces a wrapping element"""
    regions = MyRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Teaser(text="Teaser 1"),
                Teaser(text="Teaser 2"),
                Text(text="Text 2"),
            ]
        },
        renderer=renderer,
    )

    assert (
        regions.render("main")
        == 'Text 1<div class="teasers">Teaser 1Teaser 2</div>Text 2'
    )


def test_subregion_at_end(renderer):
    """Subregions are properly closed when subregion element is last"""
    regions = MyRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Teaser(text="Teaser 1"),
                Teaser(text="Teaser 2"),
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == 'Text 1<div class="teasers">Teaser 1Teaser 2</div>'


def test_other_subregion(renderer):
    """Switching to a different subregion closes the former and opens the latter"""
    regions = MyRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Teaser(text="Teaser 1"),
                Teaser(text="Teaser 2"),
                FAQ(text="Question"),
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == (
        'Text 1<div class="teasers">Teaser 1Teaser 2</div>'
        '<div class="faq">Question</div>'
    )


def test_explicit_exit(renderer):
    """Explicitly exiting a subregion works. More than one exit is silently
    ignored."""
    regions = MyRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Teaser(text="Teaser 1"),
                Teaser(text="Teaser 2"),
                Command(),
                Command(),  # Second exit shouldn't change anything
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == 'Text 1<div class="teasers">Teaser 1Teaser 2</div>'


def test_both_allowed(renderer):
    """Files do not specify a subregion, and therefore shouldn't influence
    the current subregion when rendered"""
    regions = MyRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                File(text="download1.pdf"),  # Allowed outside...
                Command(subregion="faq"),
                FAQ(text="Question"),
                File(text="download2.pdf"),  # ...and inside the FAQ renderer
                Text(text="Text 2"),  # Main renderer again.
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == (
        'Text 1download1.pdf<div class="faq">Questiondownload2.pdf</div>Text 2'
    )


def test_restart_subregion(renderer):
    """Restarting the subregion we're already in works correctly"""

    class RestartRegions(Regions):
        def handle_restart(self, items, context):
            first = True
            yield '<div class="stuff">'
            while True:
                yield self.renderer.render_plugin_in_context(items.popleft(), context)
                # Item isn't the first and explicitly specifies
                # subregion="restart", restart subregion
                if (
                    not first
                    and items
                    and matches(items[0], subregions={None, "restart"})
                ):
                    break

                first = False

            yield "</div>"

    restart_renderer = TemplatePluginRenderer()
    restart_renderer.register_string_renderer(Text, lambda plugin: plugin.text)
    restart_renderer.register_string_renderer(Command, "")

    regions = RestartRegions(
        contents={
            "main": [
                Text(text="before"),
                Command(subregion="restart"),
                Text(text="first"),
                Command(subregion="restart"),
                Text(text="second"),
                Command(subregion=""),
                Text(text="after"),
            ]
        },
        renderer=restart_renderer,
    )

    assert regions.render("main") == (
        'before<div class="stuff">first</div><div class="stuff">second</div>after'
    )


def test_enter_exit_with_custom_default(renderer):
    """Entering and exiting also works with a default subregion override"""

    class CustomDefaultRegions(MyRegions):
        def handle_default(self, items, context):
            yield '<div class="default">'
            yield from super().handle_default(items, context)
            yield "</div>"

    regions = CustomDefaultRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Teaser(text="Teaser 1"),
                Teaser(text="Teaser 2"),
                Text(text="Text 2"),
                Text(text="Text 3"),
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == (
        '<div class="default">Text 1</div>'
        '<div class="teasers">Teaser 1Teaser 2</div>'
        '<div class="default">Text 2Text 3</div>'
    )

    regions = CustomDefaultRegions.from_contents(
        contents={
            "main": [
                Text(text="Text 1"),
                Text(text="Text 2", subregion=""),
                Text(text="Text 3", subregion=None),
            ]
        },
        renderer=renderer,
    )

    assert regions.render("main") == '<div class="default">Text 1Text 2Text 3</div>'


def test_cache(renderer):
    """Caching really caches the values"""
    regions = MyRegions.from_contents(
        contents={"main": [Text(text="Stuff")]},
        renderer=renderer,
        cache_key=lambda region: region,
    )

    output = regions.render("main")

    regions = MyRegions.from_contents(
        contents={},  # Different contents!
        renderer=renderer,
        cache_key=lambda region: region,
    )
    assert output == regions.render("main")


def test_unknown_subregion(renderer):
    """Unknown subregions should crash the rendering"""
    regions = MyRegions.from_contents(
        contents={"main": [Text(text="Stuff"), Command(subregion="unknown")]},
        renderer=renderer,
    )

    with pytest.raises(KeyError):
        regions.render("main")


@pytest.mark.django_db
def test_standalone_renderer():
    """The renderer also works when used without a wrapping template"""
    renderer = TemplatePluginRenderer()
    renderer.register_template_renderer(
        HTML, ["renderer/html.html", "renderer/html.html"]
    )

    page = Page.objects.create(page_type="standard")
    HTML.objects.create(parent=page, ordering=10, region="main", html="<b>Hello</b>")

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context()) == "<b>Hello</b>\n"

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context({"outer": "Test"})) == "<b>Hello</b>Test\n"

    regions = Regions.from_item(page, renderer=renderer, timeout=3)
    assert regions.render("main", Context({"outer": "Test2"})) == "<b>Hello</b>Test2\n"

    regions = Regions.from_item(page, renderer=renderer, timeout=3)
    # Output stays the same.
    assert regions.render("main", Context({"outer": "Test3"})) == "<b>Hello</b>Test2\n"

    assert regions.cache_key("main") == f"testapp.page-{page.pk}-main"


@pytest.mark.django_db
def test_plugin_template_instance():
    """The renderer handles template instances, not just template paths etc."""
    renderer = TemplatePluginRenderer()
    renderer.register_template_renderer(HTML, Template("{{ plugin.html|safe }}"))
    page = Page.objects.create(page_type="standard")
    HTML.objects.create(parent=page, ordering=10, region="main", html="<b>Hello</b>")

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context()) == "<b>Hello</b>"
    assert regions.render("main", None) == "<b>Hello</b>"
