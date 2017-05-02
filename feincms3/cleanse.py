"""
HTML cleansing is by no means only useful for user generated content.
Managers also copy-paste content from word processing programs, the rich
text editor's output isn't always (almost never) in the shape we want it
to be, and a strict white-list based HTML sanitizer is the best answer
I have.
"""

from django.conf import settings

from ckeditor.fields import RichTextField
from html_sanitizer import Sanitizer


__all__ = ('CleansedRichTextField', 'cleanse_html')


sanitizer = Sanitizer(getattr(settings, 'FEINCMS3_SANITIZER_SETTINGS', {}))


def cleanse_html(html):
    """
    Pass ugly HTML, get nice HTML back.
    """
    return sanitizer.sanitize(html)


class CleansedRichTextField(RichTextField):
    """
    This is a subclass of django-ckeditor_'s ``RichTextField``. The recommended
    configuration is as follows::

        CKEDITOR_CONFIGS = {
            'default': {
                'toolbar': 'Custom',
                'format_tags': 'h1;h2;h3;p;pre',
                'toolbar_Custom': [[
                    'Format', 'RemoveFormat', '-',
                    'Bold', 'Italic', 'Subscript', 'Superscript', '-',
                    'NumberedList', 'BulletedList', '-',
                    'Anchor', 'Link', 'Unlink', '-',
                    'HorizontalRule', 'SpecialChar', '-',
                    'Source',
                ]],
            },
        }

        # Settings for feincms3.plugins.richtext.RichText
        CKEDITOR_CONFIGS['richtext-plugin'] = CKEDITOR_CONFIGS['default']

    The corresponding ``FEINCMS3_SANITIZER_SETTINGS`` configuration for
    html-sanitizer_ would look as follows::

        FEINCMS3_SANITIZER_SETTINGS = {
            'tags': {
                'a', 'h1', 'h2', 'h3', 'strong', 'em', 'p', 'ul', 'ol', 'li',
                'br', 'sub', 'sup', 'hr',
            },
            'attributes': {
                'a': ('href', 'name', 'target', 'title', 'id'),
            },
            'empty': {'hr', 'a', 'br'},
            'separate': {'a', 'p', 'li'},
            # 'add_nofollow': False,
            # 'autolink': False,
            # 'element_filters': [],
            # 'sanitize_href': sanitize_href,
        }

    At the time of writing those are the defaults of html-sanitizer_, so you
    don't have to do anything.

    If you want or require a different cleansing function, simply override
    the default with ``CleansedRichTextField(cleanse=your_function)``. The
    cleansing function receives the HTML as its first and only argument and
    returns the cleansed HTML.
    """

    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop('cleanse', cleanse_html)
        super(CleansedRichTextField, self).__init__(*args, **kwargs)

    def clean(self, value, instance):
        return self.cleanse(
            super(CleansedRichTextField, self).clean(value, instance))
