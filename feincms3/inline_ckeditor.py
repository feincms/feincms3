import json

import django
from django import forms
from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from html_sanitizer.django import get_sanitizer
from js_asset import JS


__all__ = ["InlineCKEditorField"]


CKEDITOR_JS_URL = JS(
    "https://cdn.ckeditor.com/4.20.1/full/ckeditor.js",
    {
        # "integrity": "sha384-qdzSU+GzmtYP2hzdmYowu+mz86DPHVROVcDAPdT/ePp1E8ke2z0gy7ITERtHzPmJ",  # noqa
        "crossorigin": "anonymous",
        "defer": "defer",
    },
)
CKEDITOR_CONFIG = {
    "default": {
        "format_tags": "h1;h2;h3;p",
        "toolbar": "Custom",
        "toolbar_Custom": [
            [
                "Format",
                "RemoveFormat",
                "-",
                "Bold",
                "Italic",
                "Subscript",
                "Superscript",
                "-",
                "BulletedList",
                "NumberedList",
                "-",
                "Link",
                "Unlink",
                "Anchor",
                "-",
                "HorizontalRule",
            ],
        ],
    }
}
CKEDITOR_CONFIG.update(getattr(settings, "FEINCMS3_CKEDITOR_CONFIG", {}))


class InlineCKEditorField(models.TextField):
    """
    This field uses an inline CKEditor 4 instance to edit HTML. All HTML is
    cleansed using `html-sanitizer
    <https://github.com/matthiask/html-sanitizer>`__.

    The default configuration of both ``InlineCKEditorField`` and HTML
    sanitizer only allows a heavily restricted subset of HTML. This should make
    it easier to write CSS which works for all possible combinations of content
    which can be added through Django's administration interface.

    The field supports the following keyword arguments to alter its
    configuration and behavior:

    - ``cleanse``: A callable which gets messy HTML and returns cleansed HTML.
    - ``ckeditor``: A CDN URL for CKEditor 4.
    - ``config``: Change the CKEditor 4 configuration. See the source for the
      current default.
    - ``config_name``: Alternative way of configuring the CKEditor. Uses the
      ``FEINCMS3_CKEDITOR_CONFIG`` setting.
    """

    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", None) or get_sanitizer().sanitize
        kwargs = self._extract_widget_config(kwargs)
        super().__init__(*args, **kwargs)

    def _extract_widget_config(self, kwargs):
        if "config_name" in kwargs:
            self.widget_config = {
                "ckeditor": kwargs.pop("ckeditor", None),
                "config": CKEDITOR_CONFIG[kwargs.pop("config_name")],
            }
        else:
            self.widget_config = {
                "ckeditor": kwargs.pop("ckeditor", None),
                "config": kwargs.pop("config", None),
            }
        return kwargs

    def clean(self, value, instance):
        """Run the cleaned form value through the ``cleanse`` callable"""
        return self.cleanse(super().clean(value, instance))

    def deconstruct(self):
        """Act as if we were a ``models.TextField``. Migrations do not have
        to know that's not 100% true."""
        name, path, args, kwargs = super().deconstruct()
        return (name, "django.db.models.TextField", args, kwargs)

    def formfield(self, **kwargs):
        """Ensure that forms use the ``InlineCKEditorWidget``"""
        kwargs["widget"] = InlineCKEditorWidget(**self.widget_config)
        return super().formfield(**kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """Add a ``get_*_excerpt`` method to models which returns a
        de-HTML-ified excerpt of the contents of this field"""
        super().contribute_to_class(cls, name, **kwargs)
        setattr(
            cls,
            f"get_{name}_excerpt",
            lambda self, words=10, truncate=" ...": Truncator(
                strip_tags(getattr(self, name))
            ).words(words, truncate=truncate),
        )


class InlineCKEditorWidget(forms.Textarea):
    def __init__(self, *args, **kwargs):
        self.ckeditor = kwargs.pop("ckeditor") or CKEDITOR_JS_URL
        self.config = kwargs.pop("config") or CKEDITOR_CONFIG["default"]

        attrs = kwargs.setdefault("attrs", {})
        attrs["data-inline-cke"] = id(self.config)
        if django.VERSION < (4, 2):
            attrs["data-inline-cke-dj41"] = True
        super().__init__(*args, **kwargs)

    @property
    def media(self):
        return forms.Media(
            css={"all": ["feincms3/inline-ckeditor.css"]},
            js=[
                self.ckeditor,
                JS(
                    "feincms3/inline-ckeditor.js",
                    {
                        "data-inline-cke-id": id(self.config),
                        "data-inline-cke-config": json.dumps(self.config),
                        "defer": "defer",
                    },
                ),
            ],
        )
