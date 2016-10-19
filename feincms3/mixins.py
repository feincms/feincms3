# coding=utf-8

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.utils.translation import activate, get_language, ugettext_lazy as _


class MenuMixin(models.Model):
    """
    The ``MenuMixin`` is most useful on pages where there are menus with
    differing content on a single page, for example the main navigation
    and a meta navigation (containing contact, imprint etc.)

    The page class should extend the menu mixin, and define a ``MENUS``
    variable describing the available menus::

        from django.utils.translation import ugettext_lazy as _
        from feincms3.mixins import MenuMixin
        from feincms3.pages import AbstractPage

        class Page(MenuMixin, AbstractPage):
            MENUS = (
                ('main', _('main navigation')),
                ('meta', _('meta navigation')),
            )

    The ``menu`` template tag may be used to fetch navigation entries
    from the template. See feincms3.templatetags.feincms3_pages.menu.
    """

    menu = models.CharField(
        _('menu'),
        max_length=20,
        blank=True,
        choices=(('', ''),),  # Non-empty choices for get_*_display
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
            field = sender._meta.get_field('menu')
            field.choices = sender.MENUS
            field.default = field.choices[0][0]


signals.class_prepared.connect(MenuMixin.fill_menu_choices)


class TemplateMixin(models.Model):
    """
    It is sometimes useful to have different templates for CMS models such
    as pages, articles or anything comparable. The ``TemplateMixin``
    provides a ready-made solution for selecting django-content-editor
    ``Template`` instances through Django's administration interface::

        from django.utils.translation import ugettext_lazy as _
        from content_editor.models import Template, Region
        from feincms3.mixins import TemplateMixin
        from feincms3.pages import AbstractPage

        class Page(TemplateMixin, AbstractPage):
            TEMPLATES = [
                Template(
                    key='standard',
                    title=_('standard'),
                    template_name='pages/standard.html',
                    regions=(
                        Region(key='main', title=_('Main')),
                    ),
                ),
                Template(
                    key='with-sidebar',
                    title=_('with sidebar'),
                    template_name='pages/with-sidebar.html',
                    regions=(
                        Region(key='main', title=_('Main')),
                        Region(key='sidebar', title=_('Sidebar')),
                    ),
                ),
            ]

    The selected ``Template`` instance is available using the ``template``
    property. If the value in ``template_key`` does not match any template,
    ``None`` is returned instead. django-content-editor also requires a
    ``regions`` property for its editing interface; the property returns the
    regions list from the selected template.
    """

    template_key = models.CharField(
        _('template'),
        max_length=100,
        choices=(('', ''),),  # Non-empty choices for get_*_display
    )

    class Meta:
        abstract = True

    @property
    def template(self):
        return self.TEMPLATES_DICT.get(self.template_key)

    @property
    def regions(self):
        return self.template.regions if self.template else []

    @staticmethod
    def fill_template_key_choices(sender, **kwargs):
        """
        Fills in the choices for ``menu`` from the ``MENUS`` class variable.
        This method is a receiver of Django's ``class_prepared`` signal.
        """
        if issubclass(sender, TemplateMixin) and not sender._meta.abstract:
            field = sender._meta.get_field('template_key')
            field.choices = [
                (t.key, t.title) for t in sender.TEMPLATES
            ]
            field.default = sender.TEMPLATES[0].key
            sender.TEMPLATES_DICT = {t.key: t for t in sender.TEMPLATES}


signals.class_prepared.connect(TemplateMixin.fill_template_key_choices)


class LanguageMixin(models.Model):
    """
    Pages may come in varying languages. ``LanguageMixin`` helps with that.
    It uses ``settings.LANGUAGES`` for the language selection, and sets the
    first language as default::

        from django.utils.translation import ugettext_lazy as _
        from feincms3.mixins import LanguageMixin
        from feincms3.pages import AbstractPage

        class Page(LanguageMixin, AbstractPage):
            pass

    The language itself is saved as ``language_code`` on the model. Also
    provided is a method ``activate_language`` which activates the selected
    language using ``django.utils.translation.activate`` and sets
    ``LANGUAGE_CODE`` on the request, the same things Django's
    ``LocaleMiddleware`` does::

        def page_detail(request, path):
            page = ...  # MAGIC! (or maybe get_object_or_404...)
            page.activate_language(request)

    Note that this does not persist the language across requests as Django´s
    ``django.views.i18n.set_language`` does. (``set_language`` modifies the
    session and sets cookies.)
    """

    language_code = models.CharField(
        _('language'),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGES[0][0],
    )

    class Meta:
        abstract = True

    def activate_language(self, request):
        # Do what LocaleMiddleware does.
        activate(self.language_code)
        request.LANGUAGE_CODE = get_language()


class RedirectMixin(models.Model):
    """
    The ``RedirectMixin`` allows redirecting pages to other pages or arbitrary
    URLs::

        from feincms3.mixins import RedirectMixin
        from feincms3.pages import AbstractPage

        class Page(RedirectMixin, AbstractPage):
            pass

    At most one of ``redirect_to_url`` or ``redirect_to_page`` may be set,
    never both at the same time. The actual redirecting is not provided. This
    has to be implemented in the page view::

        def page_detail(request, path):
            page = ...
            if page.redirect_to_url or page.redirect_to_page:
                return redirect(page.redirect_to_url or page.redirect_to_page)
            # Default rendering continues here.
    """

    redirect_to_url = models.CharField(
        _('Redirect to URL'),
        max_length=200,
        blank=True,
    )
    redirect_to_page = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+',
        verbose_name=_('Redirect to page'),
    )

    class Meta:
        abstract = True

    def clean(self):
        super(RedirectMixin, self).clean()

        if self.redirect_to_url and self.redirect_to_page_id:
            raise ValidationError({
                'redirect_to_url': _('Only set one redirect value.'),
            })
        if self.redirect_to_page_id:
            if self.redirect_to_page_id == self.pk:
                raise ValidationError({
                    'redirect_to_page': _('Cannot redirect to self.'),
                })
            if self.redirect_to_page.redirect_to_page_id:
                raise ValidationError({
                    'redirect_to_page': _(
                        'Do not chain redirects. The selected page redirects'
                        ' to %(title)s (%(path)s).'
                    ) % {
                        'title': self.redirect_to_page,
                        'path': self.redirect_to_page.get_absolute_url(),
                    },
                })
