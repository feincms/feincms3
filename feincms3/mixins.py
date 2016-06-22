from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import activate, get_language, ugettext_lazy as _


class MenuMixin(models.Model):
    menu = models.CharField(
        _('menu'),
        max_length=20,
        blank=True,
    )

    class Meta:
        abstract = True


@receiver(signals.class_prepared)
def _fill_menu_choices(sender, **kwargs):
    if issubclass(sender, MenuMixin) and not sender._meta.abstract:
        field = sender._meta.get_field('menu')
        field.choices = sender.MENUS
        field.default = field.choices[0][0]


class TemplatesMixin(models.Model):
    template_key = models.CharField(_('template'), max_length=100)

    class Meta:
        abstract = True

    @property
    def template(self):
        for t in self.TEMPLATES:
            if t.key == self.template_key:
                return t
        else:
            return None

    @property
    def regions(self):
        return self.template.regions if self.template else []


@receiver(signals.class_prepared)
def _fill_template_key_choices(sender, **kwargs):
    if issubclass(sender, TemplatesMixin) and not sender._meta.abstract:
        field = sender._meta.get_field('template_key')
        field.choices = [
            (t.key, t.title) for t in sender.TEMPLATES
        ]
        field.default = sender.TEMPLATES[0].key


class LanguageMixin(models.Model):
    language_code = models.CharField(
        _('language'),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGES[0][0],
    )

    class Meta:
        abstract = True

    def activate_language(self, request):
        # Do what LocaleMiddleware does.
        activate(self.language_code)
        request.LANGUAGE_CODE = get_language()
