from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html

from feincms3.plugins import external, html, richtext
from feincms3.regions import Regions
from feincms3.renderer import TemplatePluginRenderer

from .models import HTML, External, Image, Page, RichText, Snippet


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(RichText, richtext.render_richtext)
renderer.register_string_renderer(
    Image,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)
Snippet.register_with(renderer)
renderer.register_string_renderer(External, external.render_external)
renderer.register_string_renderer(HTML, html.render_html)


def page_detail(request, path=None):
    page = get_object_or_404(
        Page.objects.active(), path=("/%s/" % path) if path else "/"
    )
    page.activate_language(request)

    if page.redirect_to_url or page.redirect_to_page:
        return redirect(page.redirect_to_url or page.redirect_to_page)

    return render(
        request,
        page.template.template_name,
        {
            "page": page,
            "regions": Regions.from_item(
                item=page, renderer=renderer, inherit_from=page.ancestors().reverse()
            ),
        },
    )
