from django.db import models

try:
    from django.urls import reverse
except ImportError:  # pragma: no cover
    from django.core.urlresolvers import reverse

from mptt.models import MPTTModel

from content_editor.models import Template, Region, create_plugin_base


class AbstractRichText(models.Model):
    text = models.TextField(blank=True)

    class Meta:
        abstract = True
        verbose_name = 'rich text'


class Article(models.Model):
    title = models.CharField(max_length=200)

    regions = [
        Region(key='main', title='main region'),
        Region(key='sidebar', title='sidebar region'),
    ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'pk': self.pk})


ArticlePlugin = create_plugin_base(Article)


class RichText(AbstractRichText, ArticlePlugin):
    pass


class Download(ArticlePlugin):
    file = models.TextField()  # FileField, but charfield is easier to test.

    class Meta:
        verbose_name = 'download'
        verbose_name_plural = 'downloads'


class Bla(ArticlePlugin):
    class Meta:
        verbose_name = 'bla'


class Page(MPTTModel):
    title = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self', related_name='children', blank=True, null=True,
        on_delete=models.CASCADE)

    template = Template(
        key='test',
        regions=[
            Region(key='main', title='main region'),
            Region(key='sidebar', title='sidebar region', inherited=True),
        ],
    )

    class Meta:
        verbose_name = 'page'
        verbose_name_plural = 'pages'

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'pk': self.pk})

    @property
    def regions(self):
        return self.template.regions


PagePlugin = create_plugin_base(Page)


class PageText(AbstractRichText, PagePlugin):
    pass
