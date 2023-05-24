import warnings

from django.conf import settings
from django.core.checks import Warning
from django.db import models
from django.db.models import Q, signals
from django.utils.translation import activate, get_language, gettext_lazy as _
from tree_queries.fields import TreeNodeForeignKey

from feincms3.utils import ChoicesCharField, validation_error


class MenuMixin(models.Model):
    """
    The ``MenuMixin`` is most useful on pages where there are menus with
    differing content on a single page, for example the main navigation
    and a meta navigation (containing contact, imprint etc.)
    """

    menu = ChoicesCharField(_("menu"), max_length=100, blank=True)

    class Meta:
        abstract = True

    @staticmethod
    def fill_menu_choices(sender, **kwargs):
        """
        Fills in the choices for ``menu`` from the ``MENUS`` class variable.
        This method is a receiver of Django's ``class_prepared`` signal.
        """
        if issubclass(sender, MenuMixin) and not sender._meta.abstract:
            field = sender._meta.get_field("menu")
            field.choices = sender.MENUS
            field.default = field.choices[0][0]

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(cls._check_feincms3_menu_mixin(**kwargs))
        return errors

    @classmethod
    def _check_feincms3_menu_mixin(cls, **kwargs):
        if invalid := [
            value
            for value, _label in cls.MENUS
            if value and (value.startswith("_") or not value.isidentifier())
        ]:
            yield Warning(
                "MenuMixin menus should only use valid public Python identifiers"
                f" as keys. Invalid: {sorted(invalid)!r}.",
                obj=cls,
                id="feincms3.W005",
            )


signals.class_prepared.connect(MenuMixin.fill_menu_choices)


class TemplateMixin(models.Model):
    """
    It is sometimes useful to have different templates for CMS models such
    as pages, articles or anything comparable. The ``TemplateMixin``
    provides a ready-made solution for selecting django-content-editor
    ``Template`` instances through Django's administration interface.

    .. warning::
       You are encouraged to use the PageTypeMixin and TemplateType from
       :mod:`feincms3.applications` instead.
    """

    template_key = ChoicesCharField(_("template"), max_length=100)

    class Meta:
        abstract = True

    @property
    def template(self):
        """
        Return the selected template instance if the ``template_key`` field
        matches, or falls back to the first template in ``TEMPLATES``.
        """
        return self.TEMPLATES_DICT.get(self.template_key, self.TEMPLATES[0])

    @property
    def regions(self):
        """
        Return the selected template instances' ``regions`` attribute, falling
        back to an empty list if no template instance could be found.
        """
        return self.template.regions

    @staticmethod
    def fill_template_key_choices(sender, **kwargs):
        """
        Fills in the choices for ``menu`` from the ``MENUS`` class variable.
        This method is a receiver of Django's ``class_prepared`` signal.
        """
        if issubclass(sender, TemplateMixin) and not sender._meta.abstract:
            field = sender._meta.get_field("template_key")
            field.choices = [(t.key, t.title) for t in sender.TEMPLATES]
            field.default = sender.TEMPLATES[0].key
            sender.TEMPLATES_DICT = {t.key: t for t in sender.TEMPLATES}

            warnings.warn(
                f"{sender._meta.label} uses the TemplateMixin."
                " It is recommended to use the PageTypeMixin and TemplateType"
                " from feincms3.applications even if you're not planning to use"
                " any apps.",
                DeprecationWarning,
                stacklevel=1,
            )


signals.class_prepared.connect(TemplateMixin.fill_template_key_choices)


class LanguageMixin(models.Model):
    """
    Pages may come in varying languages. ``LanguageMixin`` helps with that.
    """

    language_code = ChoicesCharField(
        _("language"),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGES[0][0],
    )

    class Meta:
        abstract = True

    def activate_language(self, request):
        """
        ``activate()`` the page's language and set ``request.LANGUAGE_CODE``
        """
        # Do what LocaleMiddleware does.
        activate(self.language_code)
        request.LANGUAGE_CODE = get_language()


class LanguageAndTranslationOfMixin(LanguageMixin):
    """
    This object not only has a language, it may also be a translation of
    another object.
    """

    translation_of = TreeNodeForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name=_("translation of"),
        limit_choices_to={"language_code": settings.LANGUAGES[0][0]},
    )

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(cls._check_feincms3_language_and_translation_of_mixin(**kwargs))
        return errors

    @classmethod
    def _check_feincms3_language_and_translation_of_mixin(cls, **kwargs):
        unique_together = [set(fields) for fields in cls._meta.unique_together]
        if {"language_code", "translation_of"} not in unique_together:
            yield Warning(
                "Models using the LanguageAndTranslationOfMixin should ensure"
                " that only one translation can be added per language.",
                obj=cls,
                id="feincms3.W003",
                hint='Add ("language_code", "translation_of") to unique_together.',
            )

    def translations(self):
        """
        Return a queryset containing all translations of this object

        This method can be called on any object if translations have been
        defined at all, you do not have to fetch the object in the primary
        language first.
        """

        primary = (
            self.pk
            if self.language_code == settings.LANGUAGES[0][0]
            else self.translation_of_id
        )
        queryset = self.__class__._default_manager
        return (
            queryset.filter(Q(id=primary) | Q(translation_of=primary))
            if primary
            else queryset.none()
        )

    def clean_fields(self, exclude=None):
        """
        Implement the following validation rules:

        - Objects in the primary language cannot be the translation of another object
        - Objects in other languages can only reference objects in the primary
          language (this is automatically verified by Django because we're
          using ``limit_choices_to``)
        """

        super().clean_fields(exclude)

        if self.language_code == settings.LANGUAGES[0][0] and self.translation_of:
            raise validation_error(
                _(
                    "Objects in the primary language cannot be"
                    " the translation of another object."
                ),
                field="translation_of",
                exclude=exclude,
            )


class RedirectMixin(models.Model):
    """
    The ``RedirectMixin`` allows adding redirects in the page tree.
    """

    redirect_to_url = models.CharField(
        _("Redirect to URL"), max_length=1000, blank=True
    )
    redirect_to_page = TreeNodeForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name=_("Redirect to page"),
    )

    class Meta:
        abstract = True

    def get_redirect_url(self):
        """
        Return the URL for the redirect, if a redirect is configured
        """
        if self.redirect_to_url:
            return self.redirect_to_url
        elif self.redirect_to_page:
            return self.redirect_to_page.get_absolute_url()

    def clean_fields(self, exclude=None):
        """
        Ensure that redirects are configured properly.
        """
        super().clean_fields(exclude)

        if self.redirect_to_url and self.redirect_to_page_id:
            raise validation_error(
                _("Only set one redirect value."),
                field="redirect_to_url",
                exclude=exclude,
            )

        if self.redirect_to_page_id:
            if self.redirect_to_page_id == self.pk:
                raise validation_error(
                    _("Cannot redirect to self."),
                    field="redirect_to_page",
                    exclude=exclude,
                )

            if (
                self.redirect_to_page.redirect_to_url
                or self.redirect_to_page.redirect_to_page
            ):
                raise validation_error(
                    _(
                        'Do not chain redirects. The selected page "%(title)s"'
                        ' redirects to "%(path)s".'
                    )
                    % {
                        "title": self.redirect_to_page,
                        "path": self.redirect_to_page.get_redirect_url(),
                    },
                    field="redirect_to_page",
                    exclude=exclude,
                )

        if self.pk and (self.redirect_to_url or self.redirect_to_page_id):
            # Any page redirects to this page?
            other = self.__class__._default_manager.filter(redirect_to_page=self)
            if other:
                raise validation_error(
                    _(
                        "Do not chain redirects. The following pages already"
                        " redirect to this page: %(pages)s"
                    )
                    % {
                        "pages": ", ".join(
                            f"{page} ({page.get_absolute_url()})" for page in other
                        )
                    },
                    field="redirect_to_page",
                    exclude=exclude,
                )
