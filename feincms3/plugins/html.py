"""
Plugin providing a simple textarea where raw HTML, CSS and JS code can be
entered.

Most useful for people wanting to shoot themselves in the foot.
"""

from content_editor.admin import ContentEditorInline
from django import forms
from django.db import models
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _


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
    button = '<span class="material-icons">code</span>'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        fieldsets[0][1]["description"] = format_html(
            "<strong><big>{}</big></strong>",
            _(
                "Please note that the HTML must be well formed. It's your responsibility to ensure that nothing breaks now or in the future when using this plugin."
            ),
        )
        return fieldsets


def render_html(plugin, context=None, **kwargs):
    """
    Return the HTML code as safe string so that it is not escaped. Of course
    the contents are not guaranteed to be safe at all
    """
    return mark_safe(plugin.html)
