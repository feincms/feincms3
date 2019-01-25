"""
Plugin providing a simple textarea where raw HTML, CSS and JS code can be
entered.

Most useful for people wanting to shoot themselves in the foot.
"""

from django import forms
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditorInline


__all__ = ("HTML", "HTMLInline", "render_html")


class HTML(models.Model):
    """
    Raw HTML plugin
    """

    html = models.TextField(
        "HTML",
        help_text=_(
            "The content will be inserted directly into the page."
            " It is VERY important that the HTML snippet is well-formed!"
        ),
    )

    class Meta:
        abstract = True
        verbose_name = "HTML"
        verbose_name_plural = "HTML"

    def __str__(self):
        return ""


class HTMLInline(ContentEditorInline):
    """
    Just available for consistency, absolutely no difference to a standard
    ``ContentEditorInline``.
    """

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={"rows": 3, "cols": 40, "class": "vLargeTextField"}
            )
        }
    }


def render_html(plugin, **kwargs):
    """
    Return the HTML code as safe string so that it is not escaped. Of course
    the contents are not guaranteed to be safe at all
    """
    return mark_safe(plugin.html)
