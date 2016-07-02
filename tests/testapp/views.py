from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html

from content_editor.contents import contents_for_mptt_item
from content_editor.renderer import PluginRenderer

from feincms3 import plugins

from .models import Page, RichText, Image, Snippet, External


renderer = PluginRenderer()
renderer.register(
    RichText,
    plugins.render_richtext,
)
renderer.register(
    Image,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)
renderer.register(
    Snippet,
    plugins.render_snippet,
)
renderer.register(
    External,
    plugins.render_external,
)


def page_detail(request, path=None):
    page = get_object_or_404(
        Page.objects.active(),
        path='/{}/'.format(path) if path else '/',
    )
    page.activate_language(request)
    contents = contents_for_mptt_item(
        page,
        [RichText, Image, Snippet, External],
    )
    return render(request, page.template.template_name, {
        'page': page,
        'content': {
            region.key: renderer.render(contents[region.key])
            for region in page.regions
        },
    })
