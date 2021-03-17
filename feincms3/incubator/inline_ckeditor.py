import json

from django import forms
from django.db import models
from html_sanitizer.django import get_sanitizer
from js_asset import JS


def cleanse_html(html):
    """
    Pass ugly HTML, get nice HTML back.
    """
    return get_sanitizer().sanitize(html)


class InlineCKEditorField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", cleanse_html)
        super().__init__(*args, **kwargs)

    def clean(self, value, instance):
        return self.cleanse(super().clean(value, instance))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return (name, "django.db.models.TextField", args, kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = InlineCKEditorWidget
        return super().formfield(**kwargs)


DEFAULTS = {
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
CKEDITOR = JS(
    "https://cdn.ckeditor.com/4.16.0/standard/ckeditor.js",
    {
        # "integrity": "sha384-qdzSU+GzmtYP2hzdmYowu+mz86DPHVROVcDAPdT/ePp1E8ke2z0gy7ITERtHzPmJ",  # noqa
        "crossorigin": "anonymous",
        "data-ckeditor-defaults": json.dumps(DEFAULTS),
    },
    static=False,
)


class InlineCKEditorWidget(forms.Textarea):
    class Media:
        css = {"all": ["feincms3/inline-ckeditor.css"]}
        js = [CKEDITOR, "feincms3/inline-ckeditor.js"]

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["data-ckeditor"] = True
        super().__init__(*args, **kwargs)
