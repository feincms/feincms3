from __future__ import unicode_literals

from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import IntegrityError, models, transaction
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey


class NoCommitException(Exception):
    pass


@python_2_unicode_compatible
class AbstractPage(MPTTModel):
    """
    Short version: If you want to build a CMS with a hierarchical page
    structure, use this base class.

    It comes with the following fields:

    - ``parent``: (a nullable tree foreign key) and all MPTT fields
    - ``is_active``: Boolean field. The ``save()`` method ensures that inactive
      pages never have any active descendants.
    - ``title`` and ``slug``
    - ``path``: The complete path to the page, starting and ending with a
      slash. The maximum length of path (1000) should be enough for everyone
      (tm, famous last words). This field also has a unique index, which means
      that MySQL with its low limit on unique indexes will not work with this
      base class. Sorry.
    - ``static_path``: A boolean which, when ``True``, allows you to fill in
      the ``path`` field all by yourself. By default, ``save()`` ensures that
      the ``path`` fields are always composed of a concatenation of the
      parent's ``path`` with the page's own ``slug`` (with slashes of course).
      This is especially useful for root pages (set ``path`` to ``/``) or,
      when building a multilingual site, for language root pages (i.e.
      ``/en/``, ``/de/``, ``/pt-br/`` etc.)
    """
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

    def _branch_for_update(self):
        nodes = OrderedDict({self.pk: self})
        for node in self.get_descendants():
            # Assign already-updated instance:
            node.parent = nodes[node.parent_id]
            if not node.static_path:
                node.path = '{}{}/'.format(
                    node.parent.path,
                    node.slug)

            # Descendants of inactive nodes cannot be active themselves:
            if not node.parent.is_active:
                node.is_active = False
            nodes[node.id] = node
        return nodes

    def clean(self):
        """
        Check for path uniqueness problems.
        """
        if not self.static_path:
            self.path = '{}{}/'.format(
                self.parent.path if self.parent else '/',
                self.slug)

        super(AbstractPage, self).clean()

        # Skip if we don't exist yet.
        if not self.pk:
            return

        clash_candidates = self.__class__._default_manager.exclude(
            pk__in=self.get_descendants(include_self=True),
        )
        for pk, node in self._branch_for_update().items():
            if clash_candidates.filter(path=node.path).exists():
                raise ValidationError({
                    'parent': _(
                        'The page %(page)s\'s new path %(path)s would'
                        ' not be unique.'
                    ) % {
                        'page': node,
                        'path': node.path,
                    },
                })

    def save(self, *args, **kwargs):
        """save(self, ..., save_descendants=True)
        Saves the page instance, and traverses all descendants to update their
        ``path`` fields and ensure that inactive pages (``is_active=False``)
        never have any descendants with ``is_active=True``.
        """
        save_descendants = kwargs.pop('save_descendants', True)

        if not self.static_path:
            self.path = '{}{}/'.format(
                self.parent.path if self.parent else '/',
                self.slug)

        super(AbstractPage, self).save(*args, **kwargs)

        if save_descendants:
            for pk, node in self._branch_for_update().items():
                if pk == self.pk:
                    continue
                node.save(save_descendants=False)
    save.alters_data = True

    def get_absolute_url(self):
        """
        Return the page's absolute URL using ``reverse()``

        If path is ``/``, reverses ``pages:root`` without any arguments,
        alternatively reverses ``pages:page`` with an argument of ``path``.
        Note that this ``path`` is not the same as ``self.path`` -- slashes
        are stripped from the beginning and the end of the string to make
        building an URLconf more straightforward.
        """
        if self.path == '/':
            return reverse('pages:root')
        return reverse('pages:page', kwargs={'path': self.path.strip('/')})
