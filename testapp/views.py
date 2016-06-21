from django.utils.html import format_html, mark_safe
from django.views import generic

from content_editor.renderer import PluginRenderer
from content_editor.contents import contents_for_item, contents_for_mptt_item

from .models import (
    AbstractRichText, Article, RichText, Download, Bla, Page, PageText
)


renderer = PluginRenderer()
renderer.register(
    AbstractRichText,
    lambda plugin: mark_safe(plugin.text),
)
renderer.register(
    Download,
    lambda plugin: format_html(
        '<a href="{}">{}</a>',
        plugin.file,
        plugin.file,
    ),
)


class ArticleView(generic.DetailView):
    model = Article

    def get_context_data(self, **kwargs):
        return super(ArticleView, self).get_context_data(
            content=contents_for_item(
                self.object,
                [RichText, Download, Bla],
            ).render_regions(renderer),
            **kwargs)


class PageView(generic.DetailView):
    model = Page

    def get_context_data(self, **kwargs):
        return super(PageView, self).get_context_data(
            content=contents_for_mptt_item(
                self.object,
                [PageText],
            ).render_regions(renderer),
            **kwargs)
