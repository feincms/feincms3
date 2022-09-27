"""
Provides an image plugin with support for setting the primary point of
interest. This is very useful especially when cropping images. Depends on
`django-imagefield <https://django-imagefield.readthedocs.io>`__.  """

import os

from content_editor.admin import ContentEditorInline
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from imagefield.fields import ImageField, PPOIField

from feincms3.utils import upload_to


__all__ = ("Image", "ImageInline", "render_image")


class Image(models.Model):
    """
    Image plugin
    """

    image = ImageField(
        _("image"),
        upload_to=upload_to,
        width_field="width",
        height_field="height",
        ppoi_field="ppoi",
        # NOTE! You probably want to use auto_add_fields=True in your own
        # models and not worry about setting the *_field vars above.
    )
    width = models.PositiveIntegerField(
        _("image width"), blank=True, null=True, editable=False
    )
    height = models.PositiveIntegerField(
        _("image height"), blank=True, null=True, editable=False
    )
    ppoi = PPOIField(_("primary point of interest"))
    alternative_text = models.CharField(
        _("alternative text"),
        help_text=_("Describe the contents, e.g. for screenreaders."),
        max_length=1000,
        blank=True,
    )
    caption = models.CharField(_("caption"), blank=True, max_length=1000)

    class Meta:
        abstract = True
        verbose_name = _("image")
        verbose_name_plural = _("images")

    def __str__(self):
        return self.caption or os.path.basename(self.image.name)


class ImageInline(ContentEditorInline):
    """
    Image inline
    """

    button = '<span class="material-icons">insert_photo</span>'


def render_image(plugin, **kwargs):
    """
    Return a simple, unscaled version of the image
    """
    return format_html('<img src="{}" alt="">', plugin.image.url)
