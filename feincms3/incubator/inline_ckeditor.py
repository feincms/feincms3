from django import forms
from django.db import models
from html_sanitizer.django import get_sanitizer


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


class InlineCKEditorWidget(forms.Textarea):
    class Media:
        css = {"all": ["feincms3/inline-ckeditor.css"]}
        js = [
            "https://cdn.ckeditor.com/4.16.0/standard/ckeditor.js",
            "feincms3/inline-ckeditor.js",
        ]

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["data-ckeditor"] = True
        super().__init__(*args, **kwargs)
