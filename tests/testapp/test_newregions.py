from content_editor.models import SimpleNamespace  # types.SimpleNamespace
from django.test import TestCase

from feincms3.regions import Regions, matches
from feincms3.renderer import TemplatePluginRenderer


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


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(Text, lambda plugin: plugin.text)
renderer.register_string_renderer(Teaser, lambda plugin: plugin.text)
renderer.register_string_renderer(FAQ, lambda plugin: plugin.text)
renderer.register_string_renderer(File, lambda plugin: plugin.text)
renderer.register_string_renderer(Command, "")


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


class Test(TestCase):
    def test_enter_exit(self):
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

        self.assertEqual(
            regions.render("main"),
            'Text 1<div class="teasers">Teaser 1Teaser 2</div>Text 2',
        )

    def test_subregion_at_end(self):
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

        self.assertEqual(
            regions.render("main"), 'Text 1<div class="teasers">Teaser 1Teaser 2</div>'
        )

    def test_other_subregion(self):
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

        self.assertEqual(
            regions.render("main"),
            'Text 1<div class="teasers">Teaser 1Teaser 2</div>'
            '<div class="faq">Question</div>',
        )

    def test_explicit_exit(self):
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

        self.assertEqual(
            regions.render("main"), 'Text 1<div class="teasers">Teaser 1Teaser 2</div>'
        )

    def test_both_allowed(self):
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

        self.assertEqual(
            regions.render("main"),
            'Text 1download1.pdf<div class="faq">Questiondownload2.pdf</div>Text 2',
        )

    def test_restart_subregion(self):
        """Restarting the subregion we're already in works correctly"""

        class RestartRegions(Regions):
            def handle_restart(self, items, context):
                first = True
                yield '<div class="stuff">'
                while True:
                    yield self.renderer.render_plugin_in_context(
                        items.popleft(), context
                    )
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

        self.assertEqual(
            regions.render("main"),
            'before<div class="stuff">first</div><div class="stuff">second</div>after',
        )

    def test_enter_exit_with_custom_default(self):
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

        self.assertEqual(
            regions.render("main"),
            '<div class="default">Text 1</div>'
            '<div class="teasers">Teaser 1Teaser 2</div>'
            '<div class="default">Text 2Text 3</div>',
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

        self.assertEqual(
            regions.render("main"), '<div class="default">Text 1Text 2Text 3</div>'
        )

    def test_cache(self):
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
        self.assertEqual(output, regions.render("main"))

    def test_unknown_subregion(self):
        """Unknown subregions should crash the rendering"""
        regions = MyRegions.from_contents(
            contents={"main": [Text(text="Stuff"), Command(subregion="unknown")]},
            renderer=renderer,
        )

        with self.assertRaises(KeyError):
            regions.render("main")
