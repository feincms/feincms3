from __future__ import unicode_literals

from django.db import models
from django.db.models import signals
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


__all__ = ('Snippet', 'render_snippet')


def render_snippet(plugin):
    return render_to_string(plugin.template_name, {'plugin': plugin})


@python_2_unicode_compatible
class Snippet(models.Model):
    template_name = models.CharField(
        _('template name'),
        max_length=200,
    )

    class Meta:
        abstract = True
        verbose_name = _('snippet')
        verbose_name_plural = _('snippets')

    def __str__(self):
        return self.get_template_name_display()


def _fill_template_name_choices(sender, **kwargs):
    if issubclass(sender, Snippet) and not sender._meta.abstract:
        sender._meta.get_field('template_name').choices = sender.TEMPLATES

signals.class_prepared.connect(_fill_template_name_choices)
