"""
TODO: Give a high-level overview of the apps code.
"""

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
    """
    Tries reversing a list of viewnames with the same arguments, and returns
    the first result where no ``NoReverseMatch`` exception is raised.

    The ``NoReverseMatch`` exception of the last viewname is passed on if
    reversing fails for all viewnames.

    Usage::

        url = reverse_any((
            'blog:article-detail',
            'articles:article-detail',
        ), kwargs={'slug': 'article-slug'})
    """

    for viewname in viewnames[:-1]:
        try:
            return reverse(viewname, *args, **kwargs)
        except NoReverseMatch:
            pass

    # Let the exception bubble for the last viewname
    return reverse(viewnames[-1], *args, **kwargs)


def reverse_app(namespaces, viewname, *args, **kwargs):
    """
    Reverse app URLs, preferring the active language.

    ``reverse_app`` first generates a list of viewnames and passes them on
    to ``reverse_any``.

    Assuming that we're trying to reverse the URL of an article detail view,
    that the project is configured with german, english and french as available
    languages, french as active language and that the current article is a
    publication, the viewnames are:

    - ``fr.publications.article-detail``
    - ``fr.articles.article-detail``
    - ``de.publications.article-detail``
    - ``de.articles.article-detail``
    - ``en.publications.article-detail``
    - ``en.articles.article-detail``

    reverse_app tries harder returning an URL in the correct language than
    returning an URL for the correct instance namespace.

    Example::

        url = reverse_app(
            ('category-1', 'blog'),
            'post-detail',
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
    """
    Yields the passed class and all its subclasses in depth-first order
    """

    yield cls
    for scls in cls.__subclasses__():
        # yield from _iterate_subclasses(scls)
        for sscls in _iterate_subclasses(scls):  # PY2 :-(
            yield sscls


#: The first non-abstract subclass of AppsMixin is what we're using.
page_model = SimpleLazyObject(lambda: next(
    c for c in _iterate_subclasses(AppsMixin) if not c._meta.abstract
))


def apps_urlconf():
    """
    Generates a dynamic URLconf Python module including all applications in
    their assigned place and falling through to the default ``ROOT_URLCONF``
    at the end. Returns the value of ``ROOT_URLCONF`` directly if there are
    no active applications.

    Since Django uses an LRU cache for URL resolvers, we try hard to only
    generate a changed URLconf when application URLs actually change.

    The application URLconfs are put in nested namespaces:

    - The outer namespace is the page language as instance namespace and
      ``'language-codes'`` as application namespace. The application namespace
      does not have to be used anywhere as long as you're always using
      ``reverse_app``.
    - The inner namespace is the app namespace, where the application
      namespace is defined by the app itself (assign ``app_name`` in the
      same module as ``urlpatterns``) and the instance namespace is defined
      by the application name (from ``APPLICATIONS``).

    Modules stay around as long as the Python (most of the time WSGI) process
    lives. Unloading modules is tricky and probably not worth it since the
    URLconf modules shouldn't gobble up much memory.
    """

    fields = ('path', 'application', 'app_instance_namespace', 'language_code')
    apps = page_model.objects.active().exclude(
        app_instance_namespace=''
    ).values_list(*fields).order_by(*fields)

    if not apps:
        # No point wrapping ROOT_URLCONF if there are no additional URLs
        return settings.ROOT_URLCONF

    key = ','.join(itertools.chain.from_iterable(apps))
    module_name = 'urlconf_%s' % hashlib.md5(key.encode('utf-8')).hexdigest()

    if module_name not in sys.modules:
        app_config = {
            app[0]: app[2]
            for app in page_model.APPLICATIONS if app[0]
        }

        m = types.ModuleType(str(module_name))  # str() is correct for PY2&3

        mapping = defaultdict(list)
        for path, application, app_instance_namespace, language_code in apps:
            if application not in app_config:
                continue
            mapping[language_code].append(url(
                r'^%s' % re.escape(path.lstrip('/')),
                include(
                    app_config[application]['urlconf'],
                    namespace=app_instance_namespace,
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
    """
    Returns the current page if we're inside an app. Should only be called
    while processing app views.
    """

    # Unguarded - if this fails, we shouldn't even be here.
    page = page_model.objects.get(
        language_code=request.resolver_match.namespaces[0],
        app_instance_namespace=request.resolver_match.namespaces[1],
    )
    return page


class AppsMiddleware(object):
    """
    This middleware must be put in ``MIDDLEWARE_CLASSSES``; it simply assigns
    the return value of :func:`~feincms3.apps.apps_urlconf` to
    ``request.urlconf``.
    """

    def process_request(self, request):
        request.urlconf = apps_urlconf()


class AppsMixin(models.Model):
    """
    The page class should inherit this mixin. It adds an ``application `` field
    containing the selected application, and an ``app_instance_namespace``
    field which contains the instance namespace of the application. Most of
    the time these two fields will have the same value. This mixin also ensures
    that applications can only be activated on leaf nodes in the page tree.
    Note that currently the :class:`~feincms3.mixins.LanguageMixin` is a
    required dependency of :mod:`feincms3.apps`.

    ``APPLICATIONS`` contains a list of application configurations consisting
    of:

    - Application name (used as instance namespace)
    - User-visible name
    - Options dictionary

    Available options include:

    - ``urlconf``: The path to the URLconf module for the application. Besides
      the ``urlpatterns`` list the module should probably also specify a
      ``app_name``.
    - ``required_fields``: A list of page class fields which must be non-empty
      for the application to work. The values are checked in
      ``AppsMixin.clean``.
    - ``app_instance_namespace``: A callable which receives the page instance
      as its only argument and returns a string suitable for use as an
      instance namespace.

    Usage::

        from django.utils.translation import ugettext_lazy as _
        from feincms3.apps import AppsMixin
        from feincms3.mixins import LanguageMixin
        from feincms3.pages import AbstractPage

        class Page(AppsMixin, LanguageMixin, AbstractPage):
            APPLICATIONS = [
                ('publications', _('publications'), {
                    'urlconf': 'app.articles.urls',
                }),
                ('blog', _('blog'), {
                    'urlconf': 'app.articles.urls',
                }),
                ('contact', _('contact form'), {
                    'urlconf': 'app.forms.contact_urls',
                }),
                ('teams', _('teams'), {
                    'urlconf': 'app.teams.urls',
                    'app_instance_namespace': lambda page: '%s-%s' % (
                        page.application,
                        page.team_id,
                    ),
                    'required_fields': ('team',),
                }),
            ]
    """

    application = models.CharField(
        _('application'),
        max_length=20,
        blank=True,
        choices=(('', ''),),  # Non-empty choices for get_*_display
    )
    app_instance_namespace = models.CharField(
        _('app instance namespace'),
        max_length=100,
        editable=False,
    )

    class Meta:
        abstract = True

    def application_config(self):
        try:
            return {
                app[0]: app[2]
                for app in self.APPLICATIONS if app[0]
            }[self.application]
        except KeyError:
            return None

    def save(self, *args, **kwargs):
        app_config = self.application_config() or {}
        # If app_config is empty or None, this simply sets
        # app_instance_namespace to the empty string.
        setter = app_config.get(
            'app_instance_namespace',
            lambda instance: instance.application,
        )
        self.app_instance_namespace = setter(self)

        super(AppsMixin, self).save(*args, **kwargs)
    save.alters_data = True

    def clean(self):
        """
        Checks that application nodes do not have any descendants.
        """
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

        app_config = self.application_config()
        if app_config and app_config.get('required_fields'):
            missing = [
                field for field in app_config['required_fields']
                if not getattr(self, field)
            ]
            if missing:
                raise ValidationError({
                    field: _(
                        'This field is required for the application %s.'
                    ) % (self.get_application_display(),)
                    for field in missing
                })

    @staticmethod
    def fill_application_choices(sender, **kwargs):
        """
        Fills in the choices for ``application`` from the ``APPLICATIONS``
        class variable. This method is a receiver of Django's
        ``class_prepared`` signal.
        """
        if issubclass(sender, AppsMixin) and not sender._meta.abstract:
            sender._meta.get_field('application').choices = [
                app[:2] for app in sender.APPLICATIONS
            ]

signals.class_prepared.connect(AppsMixin.fill_application_choices)
