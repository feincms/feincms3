import json

from django import forms
from django.db import models
from html_sanitizer.django import get_sanitizer
from js_asset import JS


CKEDITOR = JS(
    "https://cdn.ckeditor.com/4.16.0/full/ckeditor.js",
    {
        # "integrity": "sha384-qdzSU+GzmtYP2hzdmYowu+mz86DPHVROVcDAPdT/ePp1E8ke2z0gy7ITERtHzPmJ",  # noqa
        "crossorigin": "anonymous",
        "defer": "defer",
    },
    static=False,
)
CONFIG = {
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
            "NumberedList",
            "BulletedList",
            "-",
            "Anchor",
            "Link",
            "Unlink",
            "-",
            "HorizontalRule",
            "SpecialChar",
            "-",
            "Source",
        ],
    ],
}


def cleanse_html(html):
    """
    Pass ugly HTML, get nice HTML back.
    """
    return get_sanitizer().sanitize(html)


class InlineCKEditorField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", cleanse_html)
        self.widget_config = {
            "ckeditor": kwargs.pop("ckeditor", None),
            "config": kwargs.pop("config", None),
        }
        super().__init__(*args, **kwargs)

    def clean(self, value, instance):
        return self.cleanse(super().clean(value, instance))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return (name, "django.db.models.TextField", args, kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = InlineCKEditorWidget(**self.widget_config)
        return super().formfield(**kwargs)


class InlineCKEditorWidget(forms.Textarea):
    def __init__(self, *args, **kwargs):
        self.ckeditor = kwargs.pop("ckeditor") or CKEDITOR
        self.config = kwargs.pop("config") or CONFIG

        attrs = kwargs.setdefault("attrs", {})
        attrs["data-inline-cke"] = True
        super().__init__(*args, **kwargs)

    @property
    def media(self):
        return forms.Media(
            css={"all": ["feincms3/inline-ckeditor.css"]},
            js=[
                "admin/js/jquery.init.js",
                self.ckeditor,
                JS(
                    "feincms3/inline-ckeditor.js",
                    {
                        "data-inline-cke-config": json.dumps(self.config),
                        "defer": "defer",
                    },
                ),
            ],
        )
