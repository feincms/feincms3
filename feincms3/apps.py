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

from feincms3.utils import validation_error


__all__ = (
    "AppsMixin",
    "apps_middleware",
    "apps_urlconf",
    "page_for_app_request",
    "reverse_any",
    "reverse_app",
    "reverse_fallback",
)


_APPS_MODEL = None


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


def reverse_app(namespaces, viewname, *args, languages=None, **kwargs):
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
            ("category-1", "blog"),
            "post-detail",
            kwargs={"year": 2016, "slug": "my-cat"},
        )
    """

    if languages is None:
        current = get_language()
        languages = sorted(
            (row[0] for row in settings.LANGUAGES), key=lambda lang: lang != current
        )
    viewnames = [
        ":".join(r)
        for r in itertools.product(
            ("%s-%s" % (_APPS_MODEL.LANGUAGE_CODES_NAMESPACE, l) for l in languages),
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

        reverse_fallback("/", lambda: reverse_app(
            ("articles",),
            "article-detail",
            kwargs={"slug": self.slug},
        ))

        reverse_fallback(
            "/",
            reverse_app
            ("articles",),
            "article-detail",
            kwargs={"slug": self.slug},
        )
    """
    try:
        return fn(*args, **kwargs)
    except NoReverseMatch:
        return fallback


def apps_urlconf(*, apps=None):
    """
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

    if apps is None:
        fields = ("path", "application", "app_instance_namespace", "language_code")
        apps = (
            _APPS_MODEL._default_manager.active()
            .with_tree_fields(False)
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
        app_config = {app[0]: app[2] for app in _APPS_MODEL.APPLICATIONS if app[0]}

        m = types.ModuleType(module_name)

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
                    (instances, _APPS_MODEL.LANGUAGE_CODES_NAMESPACE),
                    namespace="%s-%s"
                    % (_APPS_MODEL.LANGUAGE_CODES_NAMESPACE, language_code),
                ),
            )
            for language_code, instances in mapping.items()
        ]

        # Append patterns from ROOT_URLCONF instead of including them because
        # i18n_patterns only work in the root URLconf.
        urlconf = import_module(settings.ROOT_URLCONF)
        m.urlpatterns += urlconf.urlpatterns
        for attribute in ["handler400", "handler403", "handler404", "handler500"]:
            if hasattr(urlconf, attribute):
                setattr(m, attribute, getattr(urlconf, attribute))
        sys.modules[module_name] = m

    return module_name


def page_for_app_request(request, *, queryset=None):
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
            return render(request, "articles/article_detail.html", {
                "article": article,
                "page": page,
            })

    It is possible to override the queryset used to fetch a page instance. The
    default implementation simply uses the first concrete subclass of
    :class:`~feincms3.apps.AppsMixin`.
    """

    if queryset is None:
        queryset = _APPS_MODEL._default_manager.with_tree_fields()
    # Unguarded - if this fails, we shouldn't even be here.
    return queryset.get(
        language_code=request.resolver_match.namespaces[0][
            len(_APPS_MODEL.LANGUAGE_CODES_NAMESPACE) + 1 :
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
      ``AppsMixin.clean_fields``.
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
                ("publications", _("publications"), {
                    "urlconf": "app.articles.urls",
                }),
                ("blog", _("blog"), {
                    "urlconf": "app.articles.urls",
                }),
                ("contact", _("contact form"), {
                    "urlconf": "app.forms.contact_urls",
                }),
                ("teams", _("teams"), {
                    "urlconf": "app.teams.urls",
                    "app_instance_namespace": lambda page: "%s-%s" % (
                        page.application,
                        page.team_id,
                    ),
                    "required_fields": ("team",),
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

        if self.application and self.children.exists():
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
                fields = ["__all__", "application"]
                fields.extend(app_config.get("required_fields", ()))
                raise ValidationError(
                    {
                        field: _("This exact app already exists.")
                        for field in fields
                        if field not in exclude
                    }
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
            global _APPS_MODEL
            _APPS_MODEL = sender


signals.class_prepared.connect(AppsMixin.fill_application_choices)
