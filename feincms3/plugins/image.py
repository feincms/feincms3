"""
Provides an image plugin with support for setting the primary point of
interest. This is very useful especially when cropping images. Depends on
`django-imagefield <https://django-imagefield.readthedocs.io>`__.  """

from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditorInline
from imagefield.fields import ImageField, PPOIField


__all__ = ("Image", "ImageInline", "render_image")


class Image(models.Model):
    """
    Image plugin
    """

    image = ImageField(
        _("image"),
        upload_to="images/%Y/%m",
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

    class Meta:
        abstract = True
        verbose_name = _("image")
        verbose_name_plural = _("images")

    def __str__(self):
        return self.image.name


class ImageInline(ContentEditorInline):
    """
    Image inline
    """

    pass


def render_image(plugin, **kwargs):
    """
    Return a simple, unscaled version of the image
    """
    return format_html('<img src="{}" alt="">', plugin.image.url)
