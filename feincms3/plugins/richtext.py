from content_editor.admin import ContentEditorInline
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from feincms3.inline_ckeditor import InlineCKEditorField


__all__ = ("RichText", "RichTextInline", "render_richtext")


class RichText(models.Model):
    """
    Rich text plugin.

    :class:`feincms3.inline_ckeditor.InlineCKEditorField` does all the heavy
    lifting.
    """

    text = InlineCKEditorField(_("text"))

    class Meta:
        abstract = True
        verbose_name = _("rich text")
        verbose_name_plural = _("rich texts")

    def __str__(self):
        return self.get_text_excerpt()


class RichTextInline(ContentEditorInline):
    button = '<span class="material-icons">notes</span>'


def render_richtext(plugin, context=None, **kwargs):
    """
    Return the text of the rich text plugin as a safe string (``mark_safe``)
    """
    return mark_safe(plugin.text)
