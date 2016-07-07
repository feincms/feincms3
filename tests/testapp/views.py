from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html

from content_editor.contents import contents_for_mptt_item

from feincms3 import plugins
from feincms3.renderer import TemplatePluginRenderer

from .models import Page, RichText, Image, Snippet, External


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(
    RichText,
    plugins.render_richtext,
)
renderer.register_string_renderer(
    Image,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)
renderer.register_template_renderer(
    Snippet,
    lambda plugin: plugin.template_name,
    lambda plugin, context: {'additional': 'context'},
)
renderer.register_string_renderer(
    External,
    plugins.render_external,
)


def page_detail(request, path=None):
    page = get_object_or_404(
        Page.objects.active(),
        path='/{}/'.format(path) if path else '/',
    )
    page.activate_language(request)
    return render(request, page.template.template_name, {
        'page': page,
        'contents': contents_for_mptt_item(page, renderer.plugins()),
        'renderer': renderer,
    })
