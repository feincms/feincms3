import re

from django.utils.html import mark_safe


YOUTUBE_RE = re.compile(
    r"""youtu(\.?)be(\.com)?/  # match youtube's domains
        (\#/)? # for mobile urls
        (embed/)?  # match the embed url syntax
        (v/)?
        (watch\?v=)?  # match the youtube page url
        (ytscreeningroom\?v=)?
        (feeds/api/videos/)?
        (user\S*[^\w\-\s])?
        (?P<code>[\w\-]{11})[a-z0-9;:@?&%=+/\$_.-]*  # match and extract
    """,
    re.I | re.X,
)
VIMEO_RE = re.compile(
    r"""vimeo\.com/(video/)?(channels/(.*/)?)?((.+)/review/)?(?P<code>[0-9]+)""",
    re.I,
)


def embed_youtube(url):
    match = re.search(YOUTUBE_RE, url)
    if not match:
        return None
    d = match.groupdict()
    return mark_safe(
        f'<div class="responsive-embed widescreen youtube">'
        f'<iframe src="https://www.youtube.com/embed/{d["code"]}"'
        f' frameborder="0" allow="autoplay; fullscreen" allowfullscreen="">'
        f"</iframe>"
        f"</div>"
    )


def embed_vimeo(url):
    match = re.search(VIMEO_RE, url)
    if not match:
        return None
    d = match.groupdict()
    return mark_safe(
        f'<div class="responsive-embed widescreen vimeo">'
        f'<iframe src="https://player.vimeo.com/video/{d["code"]}"'
        f' frameborder="0" allow="autoplay; fullscreen" allowfullscreen="">'
        f"</iframe>"
        f"</div>"
    )


def embed_video(url, *, handlers=[embed_youtube, embed_vimeo]):
    for handler in handlers:
        html = handler(url)
        if html is not None:
            return html
