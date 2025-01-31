from feincms3.embedding import embed


def test_no_handlers():
    """Embed video without handlers"""
    assert embed("stuff") is None


def test_youtube():
    """YouTube video embedding works"""
    assert (
        embed("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        == """\
<div class="responsive-embed widescreen youtube"><iframe \
src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>"""
    )

    assert (
        embed("https://youtu.be/y7-s5ZvC_2A")
        == """\
<div class="responsive-embed widescreen youtube"><iframe \
src="https://www.youtube.com/embed/y7-s5ZvC_2A?rel=0" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>"""
    )

    assert embed("https://www.youtube.com/watch?v=4zGnNmncJWg&feature=emb_title")
    assert embed(
        "https://www.youtube.com/watch?v=DYu_bGbZiiQ&list=RDJMOOG7rWTPg&index=7"
    )
    assert embed("https://www.youtube.com/watch/ZumRshfKdtM")
    assert embed("https://www.youtube.com/shorts/ZumRshfKdtM")

    assert (
        embed("https://www.youtube.com/live/ljSZ0xrJjCs")
        == """\
<div class="responsive-embed widescreen youtube"><iframe src="https://www.youtube.com/embed/ljSZ0xrJjCs?rel=0" frameborder="0" allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>"""
    )


def test_vimeo():
    """Vimeo video embedding works"""
    assert (
        embed("https://vimeo.com/455728498")
        == """\
<div class="responsive-embed widescreen vimeo"><iframe \
src="https://player.vimeo.com/video/455728498" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>"""
    )

    assert embed("https://player.vimeo.com/video/417955670")

    assert (
        embed("https://vimeo.com/12345678/3213124324")
        == """\
<div class="responsive-embed widescreen vimeo"><iframe \
src="https://player.vimeo.com/video/12345678" frameborder="0" \
allow="autoplay; fullscreen" allowfullscreen=""></iframe></div>"""
    )
