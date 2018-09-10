"""
HTML cleansing is by no means only useful for user generated content.
Managers also copy-paste content from word processing programs, the rich
text editor's output isn't always (almost never) in the shape we want it
to be, and a strict allowlist based HTML sanitizer is the best answer
I have.
"""

from ckeditor.fields import RichTextField
from html_sanitizer.django import get_sanitizer


__all__ = ("CleansedRichTextField", "cleanse_html")


def cleanse_html(html):
    """
    Pass ugly HTML, get nice HTML back.
    """
    return get_sanitizer().sanitize(html)


class CleansedRichTextField(RichTextField):
    """
    This is a subclass of `django-ckeditor
    <https://github.com/django-ckeditor/django-ckeditor>`_'s ``RichTextField``.
    The recommended configuration is as follows::

        CKEDITOR_CONFIGS = {
            "default": {
                "toolbar": "Custom",
                "format_tags": "h1;h2;h3;p;pre",
                "toolbar_Custom": [[
                    "Format", "RemoveFormat", "-",
                    "Bold", "Italic", "Subscript", "Superscript", "-",
                    "NumberedList", "BulletedList", "-",
                    "Anchor", "Link", "Unlink", "-",
                    "HorizontalRule", "SpecialChar", "-",
                    "Source",
                ]],
            },
        }

        # Settings for feincms3.plugins.richtext.RichText
        CKEDITOR_CONFIGS["richtext-plugin"] = CKEDITOR_CONFIGS["default"]

    The corresponding ``HTML_SANITIZERS`` configuration for `html-sanitizer
    <https://pypi.org/project/html-sanitizer>`_ would look as follows::

        HTML_SANITIZERS = {
            "default": {
                "tags": {
                    "a", "h1", "h2", "h3", "strong", "em", "p",
                    "ul", "ol", "li", "br", "sub", "sup", "hr",
                },
                "attributes": {
                    "a": ("href", "name", "target", "title", "id", "rel"),
                },
                "empty": {"hr", "a", "br"},
                "separate": {"a", "p", "li"},

                # Additional default settings not listed here.
            },
        }

    At the time of writing those are the defaults of html-sanitizer, so you
    don't have to do anything.

    If you want or require a different cleansing function, simply override
    the default with ``CleansedRichTextField(cleanse=your_function)``. The
    cleansing function receives the HTML as its first and only argument and
    returns the cleansed HTML.
    """

    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", cleanse_html)
        super(CleansedRichTextField, self).__init__(*args, **kwargs)

    def clean(self, value, instance):
        return self.cleanse(super(CleansedRichTextField, self).clean(value, instance))
