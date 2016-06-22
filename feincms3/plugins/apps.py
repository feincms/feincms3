from __future__ import unicode_literals

from collections import defaultdict
import hashlib
import itertools
import re
import sys
import types

from django.conf import settings
from django.conf.urls import url, include
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db import models
from django.db.models import signals
from django.utils.functional import SimpleLazyObject
from django.utils.translation import get_language, ugettext_lazy as _


__all__ = (
    'AppsMiddleware', 'AppsMixin', 'apps_urlconf', 'page_for_app_request',
    'reverse_any', 'reverse_app',
)


def reverse_any(viewnames, *args, **kwargs):
    for viewname in viewnames[:-1]:
        try:
            return reverse(viewname, *args, **kwargs)
        except NoReverseMatch:
            pass

    # Let the exception bubble for the last viewname
    return reverse(viewnames[-1], *args, **kwargs)


def reverse_app(namespaces, viewname, *args, **kwargs):
    """
    Example::

        url = reverse_app(
            (('category-1', 'blog'), 'post-detail'),
            kwargs={'year': 2016, 'slug': 'my-cat'},
        )
    """
    current = get_language()
    viewnames = [':'.join(r) for r in itertools.product(
        [current] + [
            language[0] for language in settings.LANGUAGES
            if language[0] != current
        ],
        (
            namespaces if isinstance(namespaces, (list, tuple))
            else (namespaces,)
        ),
        (viewname,),
    )]
    return reverse_any(viewnames, *args, **kwargs)


def _iterate_subclasses(cls):
    yield cls
    for scls in cls.__subclasses__():
        # yield from _iterate_subclasses(scls)
        for sscls in _iterate_subclasses(scls):  # PY2 :-(
            yield sscls


page_model = SimpleLazyObject(lambda: next(
    c for c in _iterate_subclasses(AppsMixin) if not c._meta.abstract
))


def apps_urlconf():
    apps = page_model.objects.active().exclude(application='').values_list(
        'path',
        'application',
        'language_code',
    ).order_by('path', 'application', 'language_code')

    if not apps:
        # No point wrapping ROOT_URLCONF if there are no additional URLs
        return settings.ROOT_URLCONF

    key = ','.join(itertools.chain.from_iterable(apps))
    module_name = 'urlconf_%s' % hashlib.md5(key.encode('utf-8')).hexdigest()

    if module_name not in sys.modules:
        app_config = {app[0]: app[2] for app in page_model.APPLICATIONS}

        m = types.ModuleType(str(module_name))  # str() is correct for PY2&3

        mapping = defaultdict(list)
        for path, application, language_code in apps:
            if application not in app_config:
                continue
            mapping[language_code].append(url(
                r'^%s' % re.escape(path.lstrip('/')),
                include(
                    app_config[application]['urlconf'],
                    namespace=application,
                ),
            ))

        m.urlpatterns = [url(
            r'',
            include((instances, 'language-codes'), namespace=language_code),
        ) for language_code, instances in mapping.items()] + [
            url(r'', include(settings.ROOT_URLCONF)),
        ]
        sys.modules[module_name] = m

    return module_name


def page_for_app_request(request):
    # Unguarded - if this fails, we shouldn't even be here.
    page = page_model.objects.get(
        language_code=request.resolver_match.namespaces[0],
        application=request.resolver_match.namespaces[1],
    )
    return page


class AppsMiddleware(object):
    def process_request(self, request):
        request.urlconf = apps_urlconf()


class AppsMixin(models.Model):
    application = models.CharField(
        _('application'),
        max_length=20,
        blank=True,
    )

    class Meta:
        abstract = True

    def clean(self):
        super(AppsMixin, self).clean()

        if self.parent:
            ancestors = self.parent.get_ancestors(include_self=True)
            if ancestors.exclude(application='').exists():
                raise ValidationError({
                    'parent': _(
                        'Invalid parent: Apps may not have any descendants.'
                    ),
                })

        if self.application and not self.is_leaf_node():
            raise ValidationError({
                'application': _(
                    'Apps may not have any descendants in the tree.',
                ),
            })


def _fill_application_choices(sender, **kwargs):
    if issubclass(sender, AppsMixin) and not sender._meta.abstract:
        sender._meta.get_field('application').choices = [
            app[:2] for app in sender.APPLICATIONS
        ]

signals.class_prepared.connect(_fill_application_choices)
