from django.test import TestCase

from content_editor.models import SimpleNamespace  # types.SimpleNamespace
from feincms3.renderer import TemplatePluginRenderer
from feincms3.incubator.newregions import Regions, cached_render, matches


class Text(SimpleNamespace):
    pass


class Teaser(SimpleNamespace):
    section = "teasers"


class FAQ(SimpleNamespace):
    section = "faq"


class Command(SimpleNamespace):
    section = ""


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
        while items:
            if not matches(items[0], plugins=(Command, Teaser), sections={"teasers"}):
                break
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
        yield "</div>"

    def handle_faq(self, items, context):
        yield '<div class="faq">'
        while items:
            if not matches(items[0], plugins=(Command, FAQ, File), sections={"faq"}):
                break
            yield self.renderer.render_plugin_in_context(items.popleft(), context)
        yield "</div>"


class Test(TestCase):
    def test_enter_exit(self):
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

    def test_section_at_end(self):
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

    def test_other_section(self):
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
        regions = MyRegions.from_contents(
            contents={
                "main": [
                    Text(text="Text 1"),
                    File(text="download1.pdf"),  # Allowed outside...
                    Command(section="faq"),
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

    def test_restart_section(self):
        class RestartRegions(Regions):
            def handle_restart(self, items, context):
                first = True
                yield '<div class="stuff">'
                while items:
                    # Only match explicit section="restart" or no section
                    if not matches(items[0], sections={"restart"}):
                        break
                    yield self.renderer.render_plugin_in_context(
                        items.popleft(), context
                    )
                    # Item isn't the first and explicitly specifies
                    # section="restart", restart section
                    if not first and items and matches(items[0], sections={"restart"}):
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
                    Command(section="restart"),
                    Text(text="first"),
                    Command(section="restart"),
                    Text(text="second"),
                    Command(section=""),
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

    def test_cache(self):
        regions = MyRegions.from_contents(
            contents={"main": [Text(text="Stuff")]},
            renderer=renderer,
            decorator=cached_render(cache_key=lambda region: region, timeout=15),
        )

        output = regions.render("main")

        regions = MyRegions.from_contents(
            contents={},
            renderer=renderer,
            decorator=cached_render(cache_key=lambda region: region, timeout=15),
        )
        self.assertEqual(output, regions.render("main"))
