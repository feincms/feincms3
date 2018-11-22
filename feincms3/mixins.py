# coding=utf-8

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.utils.translation import activate, get_language, ugettext_lazy as _

from tree_queries.fields import TreeNodeForeignKey

from feincms3.utils import validation_error


class MenuMixin(models.Model):
    """
    The ``MenuMixin`` is most useful on pages where there are menus with
    differing content on a single page, for example the main navigation
    and a meta navigation (containing contact, imprint etc.)
    """

    menu = models.CharField(
        _("menu"),
        max_length=20,
        blank=True,
        choices=(("", ""),),  # Non-empty choices for get_*_display
    )

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


signals.class_prepared.connect(MenuMixin.fill_menu_choices)


class TemplateMixin(models.Model):
    """
    It is sometimes useful to have different templates for CMS models such
    as pages, articles or anything comparable. The ``TemplateMixin``
    provides a ready-made solution for selecting django-content-editor
    ``Template`` instances through Django's administration interface.
    """

    template_key = models.CharField(
        _("template"),
        max_length=100,
        choices=(("", ""),),  # Non-empty choices for get_*_display
    )

    class Meta:
        abstract = True

    @property
    def template(self):
        """
        Return the selected template instance if the ``template_key`` field
        matches, or ``None``.
        """
        return self.TEMPLATES_DICT.get(self.template_key)

    @property
    def regions(self):
        """
        Return the selected template instances' ``regions`` attribute, falling
        back to an empty list if no template instance could be found.
        """
        return self.template.regions if self.template else []

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


signals.class_prepared.connect(TemplateMixin.fill_template_key_choices)


class LanguageMixin(models.Model):
    """
    Pages may come in varying languages. ``LanguageMixin`` helps with that.
    """

    language_code = models.CharField(
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


class RedirectMixin(models.Model):
    """
    The ``RedirectMixin`` allows adding redirects in the page tree.
    """

    redirect_to_url = models.CharField(_("Redirect to URL"), max_length=200, blank=True)
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

    def clean_fields(self, exclude=None):
        """
        Ensure that redirects are configured properly.
        """
        super(RedirectMixin, self).clean_fields(exclude)

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
                self.redirect_to_page.redirect_to_page_id
                or self.redirect_to_page.redirect_to_url
            ):
                raise validation_error(
                    _(
                        'Do not chain redirects. The selected page "%(title)s"'
                        ' redirects to "%(path)s".'
                    )
                    % {
                        "title": self.redirect_to_page,
                        "path": (
                            self.redirect_to_page.redirect_to_page.get_absolute_url()
                            if self.redirect_to_page.redirect_to_page
                            else self.redirect_to_page.redirect_to_url
                        ),
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
                            "%s (%s)" % (page, page.get_absolute_url())
                            for page in other
                        )
                    },
                    field="redirect_to_page",
                    exclude=exclude,
                )
