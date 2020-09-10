from django.test import TestCase

from feincms3 import embedding


class EmbeddingTest(TestCase):
    def test_no_handlers(self):
        """Embed video without handlers"""
        self.assertEqual(embedding.embed_video("stuff"), None)

    def test_youtube(self):
        """Test a youtube link"""
        self.assertEqual(
            embedding.embed_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            """\
<div class="responsive-embed widescreen youtube"><iframe \
src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )

    def test_vimeo(self):
        self.assertEqual(
            embedding.embed_video("https://vimeo.com/455728498"),
            """\
<div class="responsive-embed widescreen vimeo"><iframe \
src="https://player.vimeo.com/video/455728498" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )
