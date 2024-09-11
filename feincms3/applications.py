import contextlib
import hashlib
import itertools
import re
import sys
from collections import Counter, defaultdict
from importlib import import_module
from types import ModuleType

from asgiref.local import Local
from asgiref.sync import iscoroutinefunction
from content_editor.models import Type
from django.conf import settings
from django.core.checks import Error, Info, Warning
from django.core.exceptions import ValidationError
from django.core.signals import request_finished
from django.db import models
from django.db.models import Q, signals
from django.urls import NoReverseMatch, include, path, re_path, reverse
from django.utils.decorators import sync_and_async_middleware
from django.utils.translation import get_language, gettext_lazy as _

from feincms3.mixins import ChoicesCharField


__all__ = (
    "PageTypeMixin",
    "TemplateType",
    "ApplicationType",
    "apps_middleware",
    "apps_urlconf",
    "page_for_app_request",
    "reverse_any",
    "reverse_app",
    "reverse_fallback",
)


_APPS_MODEL = None
_sentinel = object()


def reverse_any(
    viewnames,
    urlconf=None,
    args=None,
    kwargs=None,
    fallback=_sentinel,
    *fargs,
    **fkwargs,
):
    """
    Try reversing a list of viewnames with the same arguments, and returns the
    first result where no ``NoReverseMatch`` exception is raised. Return
    ``fallback`` if it is provided and all viewnames fail to be reversed.

    Usage:

    .. code-block:: python

        url = reverse_any(
            ("blog:article-detail", "articles:article-detail"),
            kwargs={"slug": "article-slug"},
        )
    """

    for viewname in viewnames:
        try:
            return reverse(viewname, urlconf, args, kwargs, *fargs, **fkwargs)
        except NoReverseMatch:
            pass
    if fallback is not _sentinel:
        return fallback
    raise NoReverseMatch(
        "Reverse for any of '{}' with arguments '{}' and keyword arguments"
        " '{}' not found.".format("', '".join(viewnames), args or [], kwargs or {})
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
    returning an URL for the correct instance namespace. The ``fallback``
    keyword argument is supported too.

    Example:

    .. code-block:: python

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
            (
                f"{_APPS_MODEL.LANGUAGE_CODES_NAMESPACE}-{language}"
                for language in languages
            ),
            (namespaces if isinstance(namespaces, list | tuple) else (namespaces,)),
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

    The following two examples are equivalent, choose whichever you like best:

    .. code-block:: python

        reverse_fallback(
            "/",
            lambda: reverse_app(
                ("articles",),
                "article-detail",
                kwargs={"slug": self.slug},
            ),
        )

        reverse_fallback(
            "/",
            reverse_app
            ("articles",),
            "article-detail",
            kwargs={"slug": self.slug},
        )

    Note though that ``reverse_app`` supports directly specifying the fallback
    since 3.1.1:

    .. code-block:: python

        reverse_app(
            ("articles",),
            "article-detail",
            kwargs={"slug": self.slug},
            fallback="/",
        )
    """
    try:
        return fn(*args, **kwargs)
    except NoReverseMatch:
        return fallback


# Used in feincms3-sites
def _del_apps_urlconf_cache(**kwargs):
    with contextlib.suppress(AttributeError):
        del _apps_urlconf_cache.cache


_apps_urlconf_cache = Local()
request_finished.connect(_del_apps_urlconf_cache)


def apps_urlconf(*, apps=None):
    """
    Generates a dynamic URLconf Python module including all application page
    types in their assigned place and adding the ``urlpatterns`` from
    ``ROOT_URLCONF`` at the end. Returns the value of ``ROOT_URLCONF`` directly
    if there are no active application page types.

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
      by the application name (from ``TYPES``).

    Modules stay around as long as the Python (most of the time WSGI) process
    lives. Unloading modules is tricky and probably not worth it since the
    URLconf modules shouldn't gobble up much memory.

    The set of applications can be overridden by passing a list of
    ``(path, page_type, app_namespace, language_code)`` tuples.
    """

    if apps is None:
        apps = getattr(_apps_urlconf_cache, "cache", None)

        if apps is None:
            apps = _APPS_MODEL._default_manager.active().applications()
            # NOTE! We *could* cache the module_name instead but we'd still
            # have to check if the module actually exists in the local Python
            # process.
            _apps_urlconf_cache.cache = apps

    if not apps:
        # No point wrapping ROOT_URLCONF if there are no additional URLs
        return settings.ROOT_URLCONF

    return _build_apps_urlconf(apps)


async def apps_urlconf_async(*, apps=None):
    if apps is None:
        apps = getattr(_apps_urlconf_cache, "cache", None)

        if apps is None:
            fields = ("path", "page_type", "app_namespace", "language_code")
            apps = [
                row
                async for row in _APPS_MODEL._default_manager.active()
                .without_tree_fields()
                .exclude(app_namespace="")
                .values_list(*fields)
                .order_by(*fields)
            ]
            # NOTE! We *could* cache the module_name instead but we'd still
            # have to check if the module actually exists in the local Python
            # process.
            _apps_urlconf_cache.cache = apps

    if not apps:
        # No point wrapping ROOT_URLCONF if there are no additional URLs
        return settings.ROOT_URLCONF

    return _build_apps_urlconf(apps)


def _build_apps_urlconf(apps):
    key = ",".join(itertools.chain.from_iterable(apps))
    module_name = "urlconf_%s" % hashlib.md5(key.encode("utf-8")).hexdigest()

    if module_name not in sys.modules:
        types = {app.key: app for app in _APPS_MODEL.TYPES if app.get("urlconf")}

        m = ModuleType(module_name)

        mapping = defaultdict(list)
        for app_path, page_type, app_namespace, language_code in apps:
            if page_type not in types:
                continue
            mapping[language_code].append(
                re_path(
                    r"^%s" % re.escape(app_path.lstrip("/")),
                    include(types[page_type]["urlconf"], namespace=app_namespace),
                )
            )

        m.urlpatterns = [
            path(
                "",
                include(
                    (instances, _APPS_MODEL.LANGUAGE_CODES_NAMESPACE),
                    namespace=f"{_APPS_MODEL.LANGUAGE_CODES_NAMESPACE}-{language_code}",
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
    because :func:`~feincms3.applications.apps_urlconf` wouldn't have added the app
    in the first place if a matching page wouldn't exist, but still.)

    Example:

    .. code-block:: python

        def article_detail(request, slug):
            page = page_for_app_request(request)
            page.activate_language(request)
            instance = get_object_or_404(Article, slug=slug)
            return render(
                request,
                "articles/article_detail.html",
                {"article": article, "page": page},
            )

    It is possible to override the queryset used to fetch a page instance. The
    default implementation simply uses the first concrete subclass of
    :class:`~feincms3.applications.PageTypeMixin`.
    """

    if queryset is None:
        queryset = _APPS_MODEL._default_manager.active().with_tree_fields()
    # Unguarded - if this fails, we shouldn't even be here.
    return queryset.get(
        language_code=request.resolver_match.namespaces[0][
            len(_APPS_MODEL.LANGUAGE_CODES_NAMESPACE) + 1 :
        ],
        app_namespace=request.resolver_match.namespaces[1],
    )


@sync_and_async_middleware
def apps_middleware(get_response):
    """
    This middleware must be put in ``MIDDLEWARE``; it simply assigns
    the return value of :func:`~feincms3.applications.apps_urlconf` to
    ``request.urlconf``. This middleware should probably be one of the first
    since it has to run before any resolving happens.
    """

    if iscoroutinefunction(get_response):

        async def middleware(request):
            request.urlconf = await apps_urlconf_async()
            return await get_response(request)

    else:

        def middleware(request):
            request.urlconf = apps_urlconf()
            return get_response(request)

    return middleware


class TemplateType(Type):
    """
    Template page type

    Example usage:

    .. code-block:: python

        from feincms3.applications import PageTypeMixin, TemplateType
        from feincms3.pages import AbstractPage
        from content_editor.models import Region

        class Page(AbstractPage, PageTypeMixin)
            TYPES = [
                TemplateType(
                    # Required arguments
                    key="standard",
                    title="Standard page",
                    template_name="pages/standard.html",
                    regions=[
                        Region(key="main", title="Main"),
                    ],

                    # You may pass other arguments here, they will be available
                    # on ``page.type`` as-is.
                ),
            ]
    """

    _REQUIRED = {"key", "title", "template_name", "regions", "app_namespace"}

    def __init__(self, **kwargs):
        # Always setting app_namespace makes it easier for PageTypeMixin.save
        kwargs.setdefault("app_namespace", lambda instance: "")
        super().__init__(**kwargs)


class ApplicationType(Type):
    """
    Application page type

    Example usage:

    .. code-block:: python

        from feincms3.applications import PageTypeMixin, TemplateType
        from feincms3.pages import AbstractPage
        from content_editor.models import Region

        class Page(AbstractPage, PageTypeMixin)
            TYPES = [
                TemplateType(
                    # Required arguments
                    key="standard",
                    title="Standard page",
                    urlconf="path.to.urlconf.module",

                    # Optional arguments
                    template_name="pages/standard.html",
                    regions=[
                        Region(key="main", title="Main"),
                    ],
                    app_namespace=lambda page: ...,

                    # You may pass other arguments here, they will be available
                    # on ``page.type`` as-is.
                ),
            ]
    """

    _REQUIRED = {"key", "title", "urlconf", "app_namespace"}

    def __init__(self, **kwargs):
        kwargs.setdefault("template_name", "")
        kwargs.setdefault("regions", [])
        kwargs.setdefault("app_namespace", lambda instance: instance.page_type)
        super().__init__(**kwargs)


class PageTypeMixin(models.Model):
    """
    The page class should inherit this mixin. It adds a ``page_type`` field
    containing the selected page type, and an ``app_namespace`` field which
    contains the instance namespace of the application, if the type of the page
    is an application type. The field is empty e.g. for template page types.
    Note that currently the :class:`~feincms3.mixins.LanguageMixin` is a
    required dependency of :mod:`feincms3.applications`.

    ``TYPES`` contains a list of page type instances, either
    :class:`~feincms3.applications.TemplateType` or
    :class:`~feincms3.applications.ApplicationType` and maybe others in the
    future. The configuration values are specific to each type, common to all
    of them are a key (stored in the ``page_type`` field) and a user-visible
    title.

    Template types additionally require a ``template_name`` and a ``regions``
    value.

    Application types require a ``urlconf`` value and support the following
    options:

    - ``urlconf``: The path to the URLconf module for the application. Besides
      the ``urlpatterns`` list the module should probably also specify a
      ``app_name``.
    - ``required_fields``: A list of page class fields which must be non-empty
      for the application to work. The values are checked in
      ``PageTypeMixin.clean_fields``.
    - ``app_namespace``: A callable which receives the page instance
      as its only argument and returns a string suitable for use as an
      instance namespace.

    Usage::

        from content_editor.models import Region
        from django.utils.translation import gettext_lazy as _
        from feincms3.applications import PageTypeMixin
        from feincms3.mixins import LanguageMixin
        from feincms3.pages import AbstractPage

        class Page(AbstractPage, PageTypeMixin, LanguageMixin):
            TYPES = [
                # It is recommended to always put a TemplateType type first
                # because it will be the default type:
                TemplateType(
                    key="standard",
                    title=_("Standard"),
                    template_name="pages/standard.html",
                    regions=[Region(key="main", title=_("Main"))],
                ),
                ApplicationType(
                    key="publications",
                    title=_("publications"),
                    urlconf="app.articles.urls",
                ),
                ApplicationType(
                    key="blog",
                    title=_("blog"),
                    urlconf="app.articles.urls",
                ),
                ApplicationType(
                    key="contact",
                    title=_("contact form"),
                    urlconf="app.forms.contact_urls",
                ),
                ApplicationType(
                    key="teams",
                    title=_("teams"),
                    urlconf="app.teams.urls",
                    app_namespace=lambda page: f"{page.page_type}-{page.team_id}",
                    required_fields=["team"],
                ),
            ]
    """

    #: Override this to set a different name for the outer namespace.
    LANGUAGE_CODES_NAMESPACE = "apps"

    page_type = ChoicesCharField(_("page type"), max_length=100)
    app_namespace = models.CharField(
        ("app instance namespace"), max_length=100, blank=True, editable=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Updates ``app_namespace``.
        """
        self.app_namespace = self.type.app_namespace(self)
        super().save(*args, **kwargs)

    save.alters_data = True

    @property
    def type(self):
        """
        Returns the appropriate page type instance, either the selected type or
        the first type in the list of ``TYPES`` if no type is selected or if
        the type does not exist anymore.
        """
        return self.TYPES_DICT.get(self.page_type, self.TYPES[0])

    @property
    def regions(self):
        return self.type.regions

    def clean_fields(self, exclude=None):
        """
        Checks that required fields are given and that an app namespace only
        exists once per site and language.
        """
        exclude = [] if exclude is None else exclude
        super().clean_fields(exclude)

        type = self.type
        if type and type.get("required_fields"):
            missing = [
                field for field in type["required_fields"] if not getattr(self, field)
            ]
            if missing:
                error = _('This field is required for the page type "%s".') % (
                    self.get_page_type_display(),
                )
                errors = {}
                for field in missing:
                    if field in exclude:
                        errors.setdefault("__all__", []).append(f"{field}: {error}")
                    else:
                        errors[field] = error

                raise ValidationError(errors)

        if (
            type
            and (app_namespace := type.app_namespace(self))
            and self._clash_candidates()
            .filter(
                Q(app_namespace=app_namespace),
                Q(language_code=self.language_code),
                ~Q(pk=self.pk),
            )
            .exists()
        ):
            fields = ["__all__", "page_type"]
            fields.extend(type.get("required_fields", ()))
            raise ValidationError(
                {
                    field: _(
                        'The page type "{page_type}" with the specified configuration exists already.'
                    ).format(page_type=type.title)
                    for field in fields
                    if field not in exclude
                }
            )

    @staticmethod
    def fill_page_type_choices(sender, **kwargs):
        """
        Fills in the choices for ``page_type`` from the ``TYPES``
        class variable. This method is a receiver of Django's
        ``class_prepared`` signal.
        """
        if issubclass(sender, PageTypeMixin) and not sender._meta.abstract:
            field = sender._meta.get_field("page_type")
            field.choices = [(app.key, app.title) for app in sender.TYPES]
            field.default = sender.TYPES[0].key
            sender.TYPES_DICT = {app.key: app for app in sender.TYPES}
            global _APPS_MODEL  # noqa: PLW0603 allow updating the global variable
            _APPS_MODEL = sender

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(cls._check_feincms3_appsmixin_templatemixin_clash(**kwargs))
        errors.extend(cls._check_feincms3_applications(**kwargs))
        errors.extend(cls._check_feincms3_page_types(**kwargs))
        return errors

    @classmethod
    def _check_feincms3_appsmixin_templatemixin_clash(cls, **kwargs):
        from feincms3.mixins import TemplateMixin

        if not cls._meta.abstract and issubclass(cls, TemplateMixin):
            return [
                Warning(
                    f"The model {cls._meta.label} extends both"
                    " PageTypeMixin and TemplateMixin. The new PageTypeMixin includes"
                    " the functionality of the TemplateMixin, please remove"
                    " the latter, fill in ``page_type`` fields either from"
                    " ``application`` (if non-empty) or from ``template_key``,"
                    " and rename ``app_instance_namespace`` to ``app_namespace``.",
                    obj=cls,
                    id="feincms3.W002",
                )
            ]
        return []

    @classmethod
    def _check_feincms3_applications(cls, **kwargs):
        for type in cls.TYPES:
            if isinstance(type, ApplicationType):
                try:
                    module = import_module(type.urlconf)
                except ModuleNotFoundError as exc:
                    yield Error(
                        f"The application type {type.key!r} has an unimportable"
                        f" URLconf value {type.urlconf!r}: {exc}",
                        obj=cls,
                        id="feincms3.E003",
                    )
                else:
                    app_name = getattr(module, "app_name", None)
                    if type.key != app_name and not getattr(
                        module, "ignore_app_name_mismatch", False
                    ):
                        yield Info(
                            f"The URLconf module of the application type {type.key!r}"
                            f" has app_name = {app_name!r} which doesn't match"
                            " the application key.",
                            obj=cls,
                            id="feincms3.I004",
                            hint=(
                                "Silence this warning by adding"
                                " 'ignore_app_name_mismatch = True'"
                                f" to the {type.urlconf!r} module if this is expected."
                            ),
                        )

    @classmethod
    def _check_feincms3_page_types(cls, **kwargs):
        type_keys = Counter(type.key for type in cls.TYPES)
        if keys := sorted(key for key, value in type_keys.items() if value > 1):
            yield Error(
                f"Page type keys are used more than once: {', '.join(keys)}.",
                obj=cls,
                id="feincms3.E006",
            )


signals.class_prepared.connect(PageTypeMixin.fill_page_type_choices)
