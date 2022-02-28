from content_editor.models import Region, create_plugin_base
from django.db import models
from django.utils.translation import gettext_lazy as _, override

from feincms3.applications import (
    ApplicationType,
    PageTypeMixin,
    TemplateType,
    reverse_app,
)
from feincms3.incubator.root import AbstractPage
from feincms3.mixins import LanguageAndTranslationOfMixin, MenuMixin, RedirectMixin
from feincms3.plugins import external, html, image, richtext, snippet


class Page(
    # Add this first so that AbstractPage.Meta's properties are active:
    AbstractPage,
    # For adding the articles app to pages through the CMS:
    PageTypeMixin,
    # We have a main and a footer navigation (meta):
    MenuMixin,
    # We're building a multilingual CMS. (Also, feincms3.applications depends on
    # LanguageMixin currently):
    LanguageAndTranslationOfMixin,
    # Allow redirecting pages to other pages and/or arbitrary URLs:
    RedirectMixin,
):

    # MenuMixin
    MENUS = [("main", _("main")), ("footer", _("footer"))]

    # PageTypeMixin. We have two templates and four apps.
    TYPES = [
        TemplateType(
            key="standard",
            title=_("standard"),
            template_name="pages/standard.html",
            regions=(Region(key="main", title=_("Main")),),
        ),
        TemplateType(
            key="with-sidebar",
            title=_("with sidebar"),
            template_name="pages/with-sidebar.html",
            regions=(
                Region(key="main", title=_("Main")),
                Region(key="sidebar", title=_("Sidebar")),
            ),
        ),
        ApplicationType(
            key="publications",
            title=_("publications"),
            urlconf="testapp.articles_urls",
        ),
        ApplicationType(
            key="blog",
            title=_("blog"),
            urlconf="testapp.articles_urls",
        ),
        ApplicationType(
            key="importable_module",
            title="importable_module",
            urlconf="importable_module",
            required_fields=("optional", "not_editable"),
        ),
        ApplicationType(
            key="translated-articles",
            title=_("translated articles"),
            urlconf="testapp.translated_articles_urls",
        ),
    ]

    optional = models.IntegerField(blank=True, null=True)
    not_editable = models.IntegerField(blank=True, null=True, editable=False)


PagePlugin = create_plugin_base(Page)


class RichText(richtext.RichText, PagePlugin):
    pass


class Image(image.Image, PagePlugin):
    pass


class Snippet(snippet.Snippet, PagePlugin):
    TEMPLATES = [
        (
            "snippet.html",
            _("snippet"),
            lambda plugin, context: {"plugin": plugin, "additional": "context"},
        )
    ]


class External(external.External, PagePlugin):
    pass


class HTML(html.HTML, PagePlugin):
    pass


class Article(models.Model):
    title = models.CharField(_("title"), max_length=200)
    category = models.CharField(
        _("category"),
        max_length=100,
        choices=(("publications", "publications"), ("blog", "blog")),
    )

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_app(
            (self.category, "articles"), "article-detail", kwargs={"pk": self.pk}
        )


class TranslatedArticle(LanguageAndTranslationOfMixin):
    title = models.CharField(_("title"), max_length=200)

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        with override(self.language_code):
            return reverse_app("translated-articles", "detail", kwargs={"pk": self.pk})
