"""
Provides a rich text area whose content is automatically cleaned using a
very restrictive allowlist of tags and attributes.

Depends on django-ckeditor and `html-sanitizer
<https://pypi.org/project/html-sanitizer>`__.
"""
from django.db import models
from django.utils.html import mark_safe, strip_tags
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditorInline
from feincms3.cleanse import CleansedRichTextField


__all__ = ("RichText", "RichTextInline", "render_richtext")


class RichText(models.Model):
    """
    Rich text plugin

    To use this, a `django-ckeditor
    <https://github.com/django-ckeditor/django-ckeditor>`_ configuration named
    ``richtext-plugin`` is required. See the section :mod:`HTML cleansing
    <feincms3.cleanse>` for the recommended configuration.
    """

    text = CleansedRichTextField(_("text"), config_name="richtext-plugin")

    class Meta:
        abstract = True
        verbose_name = _("rich text")
        verbose_name_plural = _("rich texts")

    def __str__(self):
        # Return the first few words of the content (with tags stripped)
        return Truncator(strip_tags(self.text)).words(10, truncate=" ...")


class RichTextInline(ContentEditorInline):
    """
    The only difference with the standard ``ContentEditorInline`` is that this
    inline adds the ``feincms3/plugin_ckeditor.js`` file which handles the
    CKEditor widget activation and deactivation inside the content editor.
    """

    class Media:
        js = ["admin/js/jquery.init.js", "feincms3/plugin_ckeditor.js"]


def render_richtext(plugin, **kwargs):
    """
    Return the text of the rich text plugin as a safe string (``mark_safe``)
    """
    return mark_safe(plugin.text)
