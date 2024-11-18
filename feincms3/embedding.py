"""
Embedding videos and other 3rd party content without oEmbed.
"""

import re
from urllib import parse

from django.utils.html import mark_safe


__all__ = ("embed_youtube", "embed_vimeo", "embed")


YOUTUBE_RE = re.compile(
    r"""youtu(\.?)be(\.com)?/  # match youtube's domains
        (\#/)? # for mobile urls
        (embed/|shorts/|watch/|live/)?  # match the embed/shorts/watch url syntax
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
SRF_RE = [
    re.compile(r)
    for r in (
        r"(https?:)?\/\/(www\.)?(srf\.ch\/play|tp\.srgssr\.ch\/p)\/(?P<type>radio|tv).*?id=.*",
        r"(https?:)?\/\/(www\.)?(srf\.ch\/play|tp\.srgssr\.ch\/p)\/(?P<type>radio|tv)/redirect/detail/(?P<id>[\w\-]+)",
        r"(https?:)?\/\/(www\.)?(srf\.ch\/play|tp\.srgssr\.ch\/p)\/.*?urn=urn:(?P<business_unit>srf|rtr|rts):(?P<type>.*?):(?P<id>[\w\-]+)",
    )
]


def embed_youtube(url):
    """
    Return HTML for embedding YouTube videos or ``None``, if argument isn't a
    YouTube link.

    The YouTube ``<iframe>`` is wrapped in a
    ``<div class="responsive-embed widescreen youtube">`` element.
    """
    match = YOUTUBE_RE.search(url)
    if not match:
        return None
    d = match.groupdict()
    return mark_safe(
        f'<div class="responsive-embed widescreen youtube">'
        f'<iframe src="https://www.youtube.com/embed/{d["code"]}?rel=0"'
        f' frameborder="0" allow="autoplay; fullscreen" allowfullscreen="">'
        f"</iframe>"
        f"</div>"
    )


def embed_vimeo(url):
    """
    Return HTML for embedding Vimeo videos or ``None``, if argument isn't a
    Vimeo link.

    The Vimeo ``<iframe>`` is wrapped in a
    ``<div class="responsive-embed widescreen vimeo">`` element.
    """
    match = VIMEO_RE.search(url)
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


def embed_srf(url):
    """
    Return HTML for embedding videos from SRF
    """
    try:
        match = next(filter(None, (r.search(url) for r in SRF_RE)))
    except StopIteration:
        return None

    d = match.groupdict()
    params = parse.parse_qs(parse.urlparse(url).query)

    id_ = d.get("id") or params["id"][0]
    type_ = "video" if d["type"] in ("tv", "video") else "audio"
    business_unit = d.get("business_unit", "srf")

    start = p[0] if (p := params.get("start")) else ""
    return mark_safe(
        '<div class="responsive-embed widescreen srfplay">'
        "<iframe "
        f"src='//srf.ch/play/embed?urn=urn:{business_unit}:{type_}:{id_}&start={start}' "
        f"allowfullscreen frameborder='0' name='' "
        'allow="geolocation *; autoplay; '
        "'encrypted-media\"></iframe>"
        "</div>"
    )


_default_handlers = [embed_youtube, embed_vimeo, embed_srf]


def embed(url, *, handlers=_default_handlers):
    """embed(url, *, handlers=[embed_youtube, embed_vimeo, embed_srf])
    Run a selection of embedding handlers and return the first value, or
    ``None`` if URL couldn't be processed by any handler.

    You could write your own handler converting the URL argument into a plain
    old anchor element or maybe even
    :func:`feincms3.plugins.external.oembed_html` if you wanted to fall back to
    oEmbed.
    """
    for handler in handlers:
        html = handler(url)
        if html is not None:
            return html
