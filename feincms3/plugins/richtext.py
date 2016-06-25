from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditorInline

from feincms3.cleanse import CleansedRichTextField


__all__ = ('CleansedRichTextField', 'RichText', 'RichTextInline')


@python_2_unicode_compatible
class RichText(models.Model):
    text = CleansedRichTextField(_('text'), config_name='richtext-plugin')

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def __str__(self):
        # Return the first few words of the content (with tags stripped)
        return Truncator(strip_tags(self.text)).words(10, truncate=' ...')


class RichTextInline(ContentEditorInline):
    class Media:
        js = ('app/js/plugin_ckeditor.js',)
