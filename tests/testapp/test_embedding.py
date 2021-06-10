from django.test import TestCase

from feincms3.embedding import embed


class EmbeddingTest(TestCase):
    def test_no_handlers(self):
        """Embed video without handlers"""
        self.assertEqual(embed("stuff"), None)

    def test_youtube(self):
        """YouTube video embedding works"""
        self.assertEqual(
            embed("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            """\
<div class="responsive-embed widescreen youtube"><iframe \
src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )

        self.assertEqual(
            embed("https://youtu.be/y7-s5ZvC_2A"),
            """\
<div class="responsive-embed widescreen youtube"><iframe \
src="https://www.youtube.com/embed/y7-s5ZvC_2A?rel=0" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )

        self.assertTrue(
            embed("https://www.youtube.com/watch?v=4zGnNmncJWg&feature=emb_title")
        )
        self.assertTrue(
            embed(
                "https://www.youtube.com/watch?v=DYu_bGbZiiQ&list=RDJMOOG7rWTPg&index=7"
            )
        )

    def test_vimeo(self):
        """Vimeo video embedding works"""
        self.assertEqual(
            embed("https://vimeo.com/455728498"),
            """\
<div class="responsive-embed widescreen vimeo"><iframe \
src="https://player.vimeo.com/video/455728498" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )

        self.assertTrue(embed("https://player.vimeo.com/video/417955670"))

        self.assertEqual(
            embed("https://vimeo.com/12345678/3213124324"),
            """\
<div class="responsive-embed widescreen vimeo"><iframe \
src="https://player.vimeo.com/video/12345678" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>""",
        )
