from django.test import TestCase

from content_editor.models import SimpleNamespace  # types.SimpleNamespace
from feincms3.renderer import TemplatePluginRenderer
from feincms3.incubator.subrenderer import Subrenderer, SubrendererRegions


class Text(SimpleNamespace):
    pass


class Teaser(SimpleNamespace):
    subrenderer = "teasers"


class FAQ(SimpleNamespace):
    subrenderer = "faq"


class Command(SimpleNamespace):
    subrenderer = ""


class File(SimpleNamespace):
    pass


class TeaserRenderer(Subrenderer):
    def enter(self, **kwargs):
        return '<div class="teasers">'

    def exit(self, **kwargs):
        return "</div>"


class FAQRenderer(Subrenderer):
    def enter(self, **kwargs):
        return '<div class="faq">'

    def exit(self, **kwargs):
        return "</div>"


teaser_renderer = TeaserRenderer()
teaser_renderer.register_string_renderer(Teaser, lambda plugin: plugin.text)
teaser_renderer.register_string_renderer(Command, "")

faq_renderer = FAQRenderer()
faq_renderer.register_string_renderer(FAQ, lambda plugin: plugin.text)
faq_renderer.register_string_renderer(Command, "")
faq_renderer.register_string_renderer(File, lambda plugin: plugin.text)


class Regions(SubrendererRegions):
    subrenderers = {"teasers": teaser_renderer, "faq": faq_renderer}


renderer = TemplatePluginRenderer(regions_class=Regions)
renderer.register_string_renderer(Text, lambda plugin: plugin.text)
renderer.register_string_renderer(Teaser, "")
renderer.register_string_renderer(FAQ, "")
renderer.register_string_renderer(Command, "")
renderer.register_string_renderer(File, lambda plugin: plugin.text)


class Test(TestCase):
    def test_enter_exit(self):
        regions = Regions(
            item=None,
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

    def test_subrenderer_at_end(self):
        regions = Regions(
            item=None,
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

    def test_other_subrenderer(self):
        regions = Regions(
            item=None,
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
        regions = Regions(
            item=None,
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
        regions = Regions(
            item=None,
            contents={
                "main": [
                    Text(text="Text 1"),
                    File(text="download1.pdf"),  # Allowed outside...
                    Command(subrenderer="faq"),
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
