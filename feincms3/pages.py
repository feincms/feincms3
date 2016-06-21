from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey
from mptt.signals import node_moved


@python_2_unicode_compatible
class AbstractPage(MPTTModel):
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True, related_name='children', db_index=True)
    is_active = models.BooleanField(_('is active'), default=True)
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'))

    # Who even cares about MySQL
    path = models.CharField(
        _('path'), max_length=1000, blank=True, unique=True,
        help_text=_('Generated automatically if \'static path\' is unset.'),
        validators=[RegexValidator(
            regex=r'^/(|.+/)$',
            message=_('Path must start and end with a slash (/).'),
        )])
    static_path = models.BooleanField(_('static path'), default=False)

    class Meta:
        abstract = True
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        save_descendants = kwargs.pop('save_descendants', True)

        if not self.static_path:
            self.path = '{0}{1}/'.format(
                self.parent.path if self.parent else '/',
                self.slug)

        super(AbstractPage, self).save(*args, **kwargs)
        if save_descendants:
            nodes = {self.pk: self}
            for node in self.get_descendants():
                # Assign already-saved instance
                node.parent = nodes[node.parent_id]
                # Descendants of inactive nodes cannot be active themselves.
                if not node.parent.is_active:
                    node.is_active = False
                node.save(save_descendants=False)
                nodes[node.id] = node
    save.alters_data = True

    def get_absolute_url(self):
        if self.path == '/':
            return reverse('pages:root')
        return reverse('pages:page', kwargs={'path': self.path.strip('/')})


@receiver(node_moved)
def handle_node_moved(instance, **kwargs):
    print(instance, kwargs)
    if not instance._meta.abstract and 'position' in kwargs:
        # We were called from move_node, not from save()
        instance.save()


class MenuMixin(models.Model):
    menu = models.CharField(
        _('menu'),
        max_length=20,
        blank=True,
    )

    class Meta:
        abstract = True


@receiver(signals.class_prepared)
def _fill_in_menu_choices(sender, **kwargs):
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
def _fill_template_choices(sender, **kwargs):
    if issubclass(sender, TemplatesMixin) and not sender._meta.abstract:
        field = sender._meta.get_field('template_key')
        field.choices = [
            (t.key, t.title) for t in sender.TEMPLATES
        ]
        field.default = sender.TEMPLATES[0].key
