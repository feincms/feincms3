from django.db import models
from django.utils.translation import ugettext_lazy as _

from content_editor.models import Region, Template, create_plugin_base
from cte_forest.models import CTENodeManager
from feincms3 import plugins
from feincms3.apps import AppsMixin, reverse_app
from feincms3.mixins import (
    LanguageMixin, MenuMixin, RedirectMixin, TemplateMixin,
)
from feincms3.pages import AbstractPage
from feincms3_images.plugins import ImageBase


class PageManager(CTENodeManager):
    def active(self):
        return self.filter(is_active=True)


class Page(
    AbstractPage,
    AppsMixin,      # For adding the articles app to pages through the CMS.
    TemplateMixin,  # Two page templates, one with only a main
                    # region and another with a sidebar as well.
    MenuMixin,      # We have a main and a footer navigation (meta).
    LanguageMixin,  # We're building a multilingual CMS. (Also,
                    # feincms3.apps depends on LanguageMixin
                    # currently.)
    RedirectMixin,  # Allow redirecting pages to other pages and/or arbitrary
                    # URLs.
):

    # TemplateMixin
    TEMPLATES = [
        Template(
            key='standard',
            title=_('standard'),
            template_name='pages/standard.html',
            regions=(
                Region(key='main', title=_('Main')),
            ),
        ),
        Template(
            key='with-sidebar',
            title=_('with sidebar'),
            template_name='pages/with-sidebar.html',
            regions=(
                Region(key='main', title=_('Main')),
                Region(key='sidebar', title=_('Sidebar')),
            ),
        ),
    ]

    # MenuMixin
    MENUS = [
        ('main', _('main')),
        ('footer', _('footer')),
    ]

    # AppsMixin. We have two apps, one is for company PR, the other
    # for a more informal blog.
    #
    # NOTE! The app names (first element in the tuple) have to match the
    # article categories exactly for URL reversing and filtering articles by
    # app to work! (See app.articles.models.Article.CATEGORIES)
    APPLICATIONS = [
        ('publications', _('publications'), {
            'urlconf': 'testapp.articles_urls',
        }),
        ('blog', _('blog'), {
            'urlconf': 'testapp.articles_urls',
        }),
    ]

    objects = PageManager()


PagePlugin = create_plugin_base(Page)


class RichText(plugins.RichText, PagePlugin):
    pass


class Image(ImageBase, PagePlugin):
    caption = models.CharField(
        _('caption'),
        max_length=200,
        blank=True,
    )


class Snippet(plugins.Snippet, PagePlugin):
    TEMPLATES = [
        ('snippet.html', _('snippet')),
    ]


class External(plugins.External, PagePlugin):
    pass


class HTML(plugins.HTML, PagePlugin):
    pass


class Article(models.Model):
    title = models.CharField(_('title'), max_length=100)
    category = models.CharField(_('category'), max_length=20, choices=(
        ('publications', 'publications'),
        ('blog', 'blog'),
    ))

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_app(
            (self.category, 'articles'),
            'article-detail',
            kwargs={'pk': self.pk},
        )
