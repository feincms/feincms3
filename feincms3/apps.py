"""
Embed apps into a pages hierarchy

This module allows content managers to freely place pre-defined applications at
(almost) arbitrary locations in the page tree. Examples for apps include forms
or a news app with archives, detail pages etc.

Apps are defined by a list of URL patterns specific to this app. A simple
contact form would probably only have a single URLconf entry (``r'^$'``), the
news app would at least have two entries (the archive and the detail URL).

The activation of apps happens through a dynamically created URLconf module
(probably the trickiest code in all of feincms3,
:func:`~feincms3.apps.apps_urlconf`). The
:class:`~feincms3.apps.AppsMiddleware` assigns the module to
``request.urlconf`` which ensures that apps are available. No page code runs at
all, control is directly passed to the app views. Apps are contained in nested
URLconf namespaces which allows for URL reversing using Django's ``reverse()``
mechanism. The inner namespace is the app itself, the outer namespace the
language. (Currently the apps code depends on
:class:`~feincms3.mixins.LanguageMixin` and cannot be used without it.)
:func:`~feincms3.apps.reverse_app` hides a good part of the complexity of
finding the best match for a given view name since apps will often be added
several times in different parts of the tree, especially on sites with more
than one language.

Please note that apps do not have to take over the page where the app itself is
attached. If the app does not have a URLconf entry for ``r'^$'`` the standard
page rendering still happens.
"""

from collections import defaultdict
import hashlib
from importlib import import_module
import itertools
import re
import sys
import types

from django.conf import settings
from django.conf.urls import url, include
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, signals
from django.utils.translation import get_language, ugettext_lazy as _
try:
    from django.urls import NoReverseMatch, reverse
except ImportError:  # pragma: no cover
    # Django <1.10
    from django.core.urlresolvers import NoReverseMatch, reverse
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # pragma: no cover
    class MiddlewareMixin(object):
        pass

from feincms3.utils import concrete_model


__all__ = (
    'AppsMiddleware', 'AppsMixin', 'apps_urlconf', 'page_for_app_request',
    'reverse_any', 'reverse_app', 'reverse_fallback',
)


def reverse_any(viewnames, urlconf=None, args=None, kwargs=None,
                *fargs, **fkwargs):
    """
    Tries reversing a list of viewnames with the same arguments, and returns
    the first result where no ``NoReverseMatch`` exception is raised.

    Usage::

        url = reverse_any((
            'blog:article-detail',
            'articles:article-detail',
        ), kwargs={'slug': 'article-slug'})
    """

    for viewname in viewnames:
        try:
            return reverse(viewname, urlconf, args, kwargs, *fargs, **fkwargs)
        except NoReverseMatch:
            pass

    raise NoReverseMatch(
        "Reverse for any of '%s' with arguments '%s' and keyword arguments"
        " '%s' not found." % (
            "', '".join(viewnames),
            args or [],
            kwargs or {}))


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


def reverse_fallback(fallback, fn, *args, **kwargs):
    """
    Returns the result of ``fn(*args, **kwargs)``, or ``fallback`` if the
    former raises an exception.
    """
    try:
        return fn(*args, **kwargs)
    except Exception:
        return fallback


def apps_urlconf():
    """
    Generates a dynamic URLconf Python module including all applications in
    their assigned place and adding the ``urlpatterns`` from ``ROOT_URLCONF``
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

    page_model = concrete_model(AppsMixin)
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

        m = types.ModuleType(str(module_name))  # Correct for Python 2 and 3

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
        ) for language_code, instances in mapping.items()]

        # Append patterns from ROOT_URLCONF instead of including them because
        # i18n_patterns only work in the root URLconf.
        m.urlpatterns += import_module(settings.ROOT_URLCONF).urlpatterns
        sys.modules[module_name] = m

    return module_name


def page_for_app_request(request):
    """
    Returns the current page if we're inside an app. Should only be called
    while processing app views. Will pass along exceptions caused by
    non-existing or duplicated apps (this should never happen inside an app
    because :func:`~feincms3.apps.apps_urlconf` wouldn't have added the app
    in the first place if a matching page wouldn't exist, but still.)

    Example::

        def article_detail(request, slug):
            page = page_for_app_request(request)
            page.activate_language(request)
            instance = get_object_or_404(Article, slug=slug)
            return render(request, 'articles/article_detail.html', {
                'article': article,
                'page': page,
            })
    """

    # Unguarded - if this fails, we shouldn't even be here.
    page = concrete_model(AppsMixin).objects.get(
        language_code=request.resolver_match.namespaces[0],
        app_instance_namespace=request.resolver_match.namespaces[1],
    )
    return page


class AppsMiddleware(MiddlewareMixin):
    """
    This middleware must be put in ``MIDDLEWARE_CLASSES``; it simply assigns
    the return value of :func:`~feincms3.apps.apps_urlconf` to
    ``request.urlconf``. This middleware should probably be one of the first
    since it has to run before any resolving happens.
    """

    def process_request(self, request):
        request.urlconf = apps_urlconf()


class AppsMixin(models.Model):
    """
    The page class should inherit this mixin. It adds an ``application`` field
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
        """
        Returns the selected application options dictionary, or ``None`` if
        no application is selected or the application does not exist anymore.
        """
        try:
            return {
                app[0]: app[2]
                for app in self.APPLICATIONS if app[0]
            }[self.application]
        except KeyError:
            return None

    def save(self, *args, **kwargs):
        """
        Updates ``app_instance_namespace``.
        """
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
        Checks that application nodes do not have any descendants, and that
        required fields for the selected application (if any) are filled out,
        and that app instances with the same instance namespace and same
        language only exist once on a site.
        """
        super(AppsMixin, self).clean()

        if self.parent:
            if (self.parent.application or
                    self.parent.ancestors().exclude(application='').exists()):
                raise ValidationError(_(
                    'Invalid parent: Apps may not have any descendants.'
                ))

        if self.application and not self.is_leaf():
            raise ValidationError(_(
                    'Apps may not have any descendants in the tree.',
            ))

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

        if app_config:
            app_instance_namespace = app_config.get(
                'app_instance_namespace',
                lambda instance: instance.application,
            )(self)

            if self.__class__._base_manager.filter(
                Q(app_instance_namespace=app_instance_namespace),
                Q(language_code=self.language_code),
                ~Q(pk=self.pk or 0),
            ).exists():
                fields = ['application']
                fields.extend(app_config.get('required_fields', ()))
                raise ValidationError({
                    field: _(
                        _('This exact app already exists.'),
                    )
                    for field in fields
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
