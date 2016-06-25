======
Models
======

Pages
=====

The pages models look as follows::

    from __future__ import unicode_literals

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from mptt.models import TreeManager

    from content_editor.models import Region, Template, create_plugin_base

    from feincms3 import plugins
    from feincms3.apps import AppsMixin
    from feincms3.mixins import TemplateMixin, MenuMixin, LanguageMixin
    from feincms3.pages import AbstractPage


    class PageQuerySet(models.QuerySet):
        def active(self):
            return self.filter(is_active=True)


    # Django 1.9. Django 1.10 will not use `use_for_related_fields` anymore.
    class PageManager(TreeManager.from_queryset(PageQuerySet)):
        use_for_related_fields = True


    class Page(
            AbstractPage,
            AppsMixin,      # For adding the articles app to pages through the CMS.
            TemplateMixin,  # Two page templates, one with only a main
                            # region and another with a sidebar as well.
            MenuMixin,      # We have a main and a footer navigation (meta).
            LanguageMixin,  # We're building a multilingual CMS. (Also,
                            # feincms3.apps depends on LanguageMixin
                            # currently.)
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
        APPLICATIONS = [
            ('publications', _('publications'), {
                'urlconf': 'app.articles.urls',
            }),
            ('blog', _('blog'), {
                'urlconf': 'app.articles.urls',
            }),
        ]

        objects = PageManager()


    PagePlugin = create_plugin_base(Page)


    class RichText(plugins.RichText, PagePlugin):
        style = models.CharField(
            _('style'),
            max_length=20,
            choices=(('default', _('default')), ('intro', _('intro'))),
            default='default',
        )


    class Image(plugins.Image, PagePlugin):
        caption = models.CharField(
            _('caption'),
            max_length=200,
            blank=True,
        )


Articles
========

The articles models. We're using the ``CleansedRichTextField`` field
which provides us with django-ckeditor_'s editing interface and
feincms-cleanse_'s HTML post-processing and cleansing. This code snippet
also contains the trickiest bit of this whole project, ``Article``'s
``get_absolute_url`` implementation::

    from __future__ import unicode_literals

    from django.db import models
    from django.utils import timezone
    from django.utils.encoding import python_2_unicode_compatible
    from django.utils.translation import ugettext_lazy as _

    from feincms3.apps import reverse_app
    from feincms3.cleanse import CleansedRichTextField
    from feincms3 import plugins


    class ArticleManager(models.Manager):
        def active(self):
            return self.filter(is_active=True)

        def published(self):
            return self.filter(
                is_active=True,
                publication_date__lte=timezone.now(),
            )


    @python_2_unicode_compatible
    class Article(models.Model):
        CATEGORIES = (
            ('publications', _('publications')),
            ('blog', _('blog')),
        )

        is_active = models.BooleanField(_('is active'), default=False)
        title = models.CharField(_('title'), max_length=200)
        slug = models.SlugField(_('slug'), unique_for_year='publication_date')
        publication_date = models.DateTimeField(
            _('publication date'), default=timezone.now)
        body = CleansedRichTextField(_('body'))
        category = models.CharField(
            _('category'),
            max_length=20,
            db_index=True,
            choices=CATEGORIES,
        )

        objects = ArticleManager()

        class Meta:
            get_latest_by = 'publication_date'
            ordering = ['-publication_date']
            verbose_name = _('article')
            verbose_name_plural = _('articles')

        def __str__(self):
            return self.title

        def get_absolute_url(self):
            # This is the trickiest bit of this whole project.
            # reverse_app is a simple wrapper around
            # feincms3.apps.reverse_any, which is exactly the same as
            # django.core.urlresolvers.reverse with the small difference
            # that it accepts a list of viewnames and returns the first
            # result where no NoReverseMatch exception is raised.
            #
            # The viewnames tried in sequence by reverse_app are
            # (assuming that the project is configured with german,
            # english and french as available languages, and french as
            # active language, and assuming that the current article is
            # a publication):
            #
            # - fr.publications.article-detail
            # - fr.articles.article-detail
            # - de.publications.article-detail
            # - de.articles.article-detail
            # - en.publications.article-detail
            # - en.articles.article-detail
            # - Otherwise, let the NoReverseMatch exception bubble.
            #
            # reverse_app tries harder returning an URL in the correct
            # language than returning an URL for the correct app. Better
            # show a PR publication on the blog page than switching
            # languages.

            return reverse_app(
                (self.category, 'articles'),
                'article-detail',
                kwargs={
                    'year': self.publication_date.year,
                    'slug': self.slug,
                },
            )


    # Yay. Let's use feincms3.plugins' versatileimagefield support.
    class Image(plugins.Image):
        article = models.ForeignKey(
            Article,
            on_delete=models.CASCADE,
            verbose_name=_('article'),
            related_name='images',
        )
        caption = models.CharField(
            _('caption'),
            max_length=200,
            blank=True,
        )


.. _django-ckeditor: https://pypi.python.org/pypi/django-ckeditor
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse
