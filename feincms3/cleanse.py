"""
HTML cleansing is by no means only useful for user generated content.
Managers also copy-paste content from word processing programs, the rich
text editor's output isn't always (almost never) in the shape we want it
to be, and a strict white-list based HTML sanitizer is the best answer
I have.
"""

from ckeditor.fields import RichTextField

from feincms_cleanse import Cleanse


__all__ = ('CleansedRichTextField', 'cleanse_html')


# Site-wide patch of cleanse settings
# -----------------------------------

Cleanse.allowed_tags['a'] += ('id', 'name')  # Allow anchors
Cleanse.allowed_tags['hr'] = ()  # Allow horizontal rules
Cleanse.allowed_tags['h1'] = ()  # Allow H1
Cleanse.empty_tags += ('hr', 'a')  # Allow empty <hr/> and anchor targets


def cleanse_html(html):
    """
    Pass ugly HTML, get nice HTML back.
    """
    return Cleanse().cleanse(html)


class CleansedRichTextField(RichTextField):
    """
    This is a subclass of django-ckeditor's ``RichTextField``. The recommended
    configuration is as follows::

        CKEDITOR_CONFIGS = {
            'default': {
                'toolbar': 'Custom',
                'format_tags': 'h1;h2;h3;p;pre',
                'toolbar_Custom': [
                    ['Format', 'RemoveFormat'],
                    ['Bold', 'Italic', 'Strike', '-',
                     'NumberedList', 'BulletedList', '-',
                     'Anchor', 'Link', 'Unlink', '-',
                     'Source'],
                ],
            },
        }

        # Settings for feincms3.plugins.richtext.RichText
        CKEDITOR_CONFIGS['richtext-plugin'] = CKEDITOR_CONFIGS['default']

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
