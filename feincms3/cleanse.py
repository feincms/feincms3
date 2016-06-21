from __future__ import unicode_literals

from ckeditor.fields import RichTextField

from feincms_cleanse import Cleanse

# Site-wide patch of cleanse settings
# -----------------------------------

Cleanse.allowed_tags['a'] += ('id', 'name')  # Allow anchors
Cleanse.allowed_tags['hr'] = ()  # Allow horizontal rules
Cleanse.allowed_tags['h1'] = ()  # Allow H1
Cleanse.empty_tags += ('hr',)
cleanse_html = Cleanse().cleanse


class CleansedRichTextField(RichTextField):
    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop('cleanse', cleanse_html)
        super(CleansedRichTextField, self).__init__(*args, **kwargs)

    def clean(self, value, instance):
        return self.cleanse(
            super(CleansedRichTextField, self).clean(value, instance))
