"""
Embed apps into a pages hierarchy

This module allows content managers to freely place pre-defined applications at
(almost) arbitrary locations in the page tree. Examples for apps include forms
or a news app with archives, detail pages etc.

Apps are defined by a list of URL patterns specific to this app. A simple
contact form would probably only have a single URLconf entry (``r'^$'``), the
news app would at least have two entries (the archive and the detail URL).
You'll find an example app for integrating form_designer_ with feincms3_ at
the end of this documentation.

The activation of apps happens through a dynamically created URLconf module
(probably the trickiest code in all of feincms3,
:func:`~feincms3.apps.apps_urlconf`). The
:class:`~feincms3.apps.apps_middleware` assigns the module to
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

import hashlib
import itertools
import re
import sys
import types
from collections import defaultdict
from importlib import import_module

from django.conf import settings
from django.conf.urls import include, url
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, signals
from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language, ugettext_lazy as _

from feincms3.utils import concrete_model, positional, validation_error


__all__ = (
    "AppsMiddleware",
    "AppsMixin",
    "apps_middleware",
    "apps_urlconf",
    "page_for_app_request",
    "reverse_any",
    "reverse_app",
    "reverse_fallback",
)


def reverse_any(viewnames, urlconf=None, args=None, kwargs=None, *fargs, **fkwargs):
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
        " '%s' not found." % ("', '".join(viewnames), args or [], kwargs or {})
    )


def reverse_app(namespaces, viewname, *args, **kwargs):
    """
    Reverse app URLs, preferring the active language.

    ``reverse_app`` first generates a list of viewnames and passes them on
    to ``reverse_any``.

    Assuming that we're trying to reverse the URL of an article detail view,
    that the project is configured with german, english and french as available
    languages, french as active language and that the current article is a
    publication, the viewnames are:

    - ``apps-fr.publications.article-detail``
    - ``apps-fr.articles.article-detail``
    - ``apps-de.publications.article-detail``
    - ``apps-de.articles.article-detail``
    - ``apps-en.publications.article-detail``
    - ``apps-en.articles.article-detail``

    reverse_app tries harder returning an URL in the correct language than
    returning an URL for the correct instance namespace.

    Example::

        url = reverse_app(
            ('category-1', 'blog'),
            'post-detail',
            kwargs={'year': 2016, 'slug': 'my-cat'},
        )
    """

    page_model = concrete_model(AppsMixin)
    current = get_language()
    viewnames = [
        ":".join(r)
        for r in itertools.product(
            ["%s-%s" % (page_model.LANGUAGE_CODES_NAMESPACE, current)]
            + [
                "%s-%s" % (page_model.LANGUAGE_CODES_NAMESPACE, language[0])
                for language in settings.LANGUAGES
                if language[0] != current
            ],
            (namespaces if isinstance(namespaces, (list, tuple)) else (namespaces,)),
            (viewname,),
        )
    ]
    return reverse_any(viewnames, *args, **kwargs)


def reverse_fallback(fallback, fn, *args, **kwargs):
    """
    Returns the result of ``fn(*args, **kwargs)``, or ``fallback`` if the
    former raises a ``NoReverseMatch`` exception. This is especially useful for
    reversing app URLs from outside the app and you do not want crashes if the
    app isn't available anywhere.

    The following two examples are equivalent, choose whichever you like best::

        reverse_fallback('/', lambda: reverse_app(
            ('articles',),
            'article-detail',
            kwargs={'slug': self.slug},
        ))

        reverse_fallback(
            '/',
            reverse_app
            ('articles',),
            'article-detail',
            kwargs={'slug': self.slug},
        )
    """
    try:
        return fn(*args, **kwargs)
    except NoReverseMatch:
        return fallback


@positional(0)
def apps_urlconf(apps=None):
    """apps_urlconf(*, apps=None)
    Generates a dynamic URLconf Python module including all applications in
    their assigned place and adding the ``urlpatterns`` from ``ROOT_URLCONF``
    at the end. Returns the value of ``ROOT_URLCONF`` directly if there are
    no active applications.

    Since Django uses an LRU cache for URL resolvers, we try hard to only
    generate a changed URLconf when application URLs actually change.

    The application URLconfs are put in nested namespaces:

    - The outer application namespace is ``apps`` by default. This value can be
      overridden by setting the ``LANGUAGE_CODES_NAMESPACE`` class attribute of
      the page class to a different value. The instance namespaces consist of
      the ``LANGUAGE_CODES_NAMESPACE`` value with a language added at the end.
      As long as you're always using ``reverse_app`` you do not have to know
      the specifics.
    - The inner namespace is the app namespace, where the application
      namespace is defined by the app itself (assign ``app_name`` in the
      same module as ``urlpatterns``) and the instance namespace is defined
      by the application name (from ``APPLICATIONS``).

    Modules stay around as long as the Python (most of the time WSGI) process
    lives. Unloading modules is tricky and probably not worth it since the
    URLconf modules shouldn't gobble up much memory.

    The set of applications can be overridden by passing a list of
    ``(path, application, app_instance_namespace, language_code)`` tuples.
    """

    page_model = concrete_model(AppsMixin)
    if apps is None:
        fields = ("path", "application", "app_instance_namespace", "language_code")
        apps = (
            page_model.objects.active()
            # TODO .with_tree_fields(False)
            .exclude(app_instance_namespace="")
            .values_list(*fields)
            .order_by(*fields)
        )

    if not apps:
        # No point wrapping ROOT_URLCONF if there are no additional URLs
        return settings.ROOT_URLCONF

    key = ",".join(itertools.chain.from_iterable(apps))
    module_name = "urlconf_%s" % hashlib.md5(key.encode("utf-8")).hexdigest()

    if module_name not in sys.modules:
        app_config = {app[0]: app[2] for app in page_model.APPLICATIONS if app[0]}

        m = types.ModuleType(str(module_name))  # Correct for Python 2 and 3

        mapping = defaultdict(list)
        for path, application, app_instance_namespace, language_code in apps:
            if application not in app_config:
                continue
            mapping[language_code].append(
                url(
                    r"^%s" % re.escape(path.lstrip("/")),
                    include(
                        app_config[application]["urlconf"],
                        namespace=app_instance_namespace,
                    ),
                )
            )

        m.urlpatterns = [
            url(
                r"",
                include(
                    (instances, page_model.LANGUAGE_CODES_NAMESPACE),
                    namespace="%s-%s"
                    % (page_model.LANGUAGE_CODES_NAMESPACE, language_code),
                ),
            )
            for language_code, instances in mapping.items()
        ]

        # Append patterns from ROOT_URLCONF instead of including them because
        # i18n_patterns only work in the root URLconf.
        m.urlpatterns += import_module(settings.ROOT_URLCONF).urlpatterns
        sys.modules[module_name] = m

    return module_name


@positional(1)
def page_for_app_request(request, queryset=None):
    """page_for_app_request(request, *, queryset=None)
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

    It is possible to override the queryset used to fetch a page instance. The
    default implementation simply uses the first concrete subclass of
    :class:`~feincms3.apps.AppsMixin`.
    """

    page_model = concrete_model(AppsMixin)
    if queryset is None:
        queryset = page_model.objects.with_tree_fields()
    # Unguarded - if this fails, we shouldn't even be here.
    return queryset.get(
        language_code=request.resolver_match.namespaces[0][
            len(page_model.LANGUAGE_CODES_NAMESPACE) + 1 :
        ],
        app_instance_namespace=request.resolver_match.namespaces[1],
    )


def apps_middleware(get_response):
    """
    This middleware must be put in ``MIDDLEWARE``; it simply assigns
    the return value of :func:`~feincms3.apps.apps_urlconf` to
    ``request.urlconf``. This middleware should probably be one of the first
    since it has to run before any resolving happens.
    """

    def middleware(request):
        request.urlconf = apps_urlconf()
        return get_response(request)

    return middleware


# Alias, for old times
AppsMiddleware = apps_middleware


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

    #: Override this to set a different name for the outer namespace.
    LANGUAGE_CODES_NAMESPACE = "apps"

    application = models.CharField(
        _("application"),
        max_length=20,
        blank=True,
        choices=(("", ""),),  # Non-empty choices for get_*_display
    )
    app_instance_namespace = models.CharField(
        _("app instance namespace"), max_length=100, editable=False
    )

    class Meta:
        abstract = True

    def application_config(self):
        """
        Returns the selected application options dictionary, or ``None`` if
        no application is selected or the application does not exist anymore.
        """
        try:
            return {app[0]: app[2] for app in self.APPLICATIONS if app[0]}[
                self.application
            ]
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
            "app_instance_namespace", lambda instance: instance.application
        )
        self.app_instance_namespace = setter(self)

        super(AppsMixin, self).save(*args, **kwargs)

    save.alters_data = True

    def clean_fields(self, exclude=None):
        """
        Checks that application nodes do not have any descendants, and that
        required fields for the selected application (if any) are filled out,
        and that app instances with the same instance namespace and same
        language only exist once on a site.
        """
        exclude = [] if exclude is None else exclude
        super(AppsMixin, self).clean_fields(exclude)

        if self.parent and (
            self.parent.application
            or self.parent.ancestors().exclude(application="").exists()
        ):
            error = _("Apps may not have any descendants.")
            raise validation_error(
                _("Invalid parent: %s") % (error,), field="parent", exclude=exclude
            )

        if self.application and not self.is_leaf():
            raise validation_error(
                _("Apps may not have any descendants in the tree."),
                field="application",
                exclude=exclude,
            )

        app_config = self.application_config()
        if app_config and app_config.get("required_fields"):
            missing = [
                field
                for field in app_config["required_fields"]
                if not getattr(self, field)
            ]
            if missing:
                error = _("This field is required for the application %s.") % (
                    self.get_application_display(),
                )
                errors = {}
                for field in missing:
                    if field in exclude:
                        errors.setdefault("__all__", []).append(
                            "%s: %s" % (field, error)
                        )
                    else:
                        errors[field] = error

                raise ValidationError(errors)

        if app_config:
            app_instance_namespace = app_config.get(
                "app_instance_namespace", lambda instance: instance.application
            )(self)

            if self.__class__._default_manager.filter(
                Q(app_instance_namespace=app_instance_namespace),
                Q(language_code=self.language_code),
                ~Q(pk=self.pk),
            ).exists():
                fields = ["application"]
                fields.extend(app_config.get("required_fields", ()))
                raise ValidationError(
                    {field: _(_("This exact app already exists.")) for field in fields}
                )

    @staticmethod
    def fill_application_choices(sender, **kwargs):
        """
        Fills in the choices for ``application`` from the ``APPLICATIONS``
        class variable. This method is a receiver of Django's
        ``class_prepared`` signal.
        """
        if issubclass(sender, AppsMixin) and not sender._meta.abstract:
            sender._meta.get_field("application").choices = [
                app[:2] for app in sender.APPLICATIONS
            ]


signals.class_prepared.connect(AppsMixin.fill_application_choices)
