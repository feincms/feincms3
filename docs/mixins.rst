============
Model mixins
============


``MenuMixin``
=============

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
from the template (this snippet expects ``page`` to be a template
context variable containing the page we're on currently)::

    {% load feincms3_pages %}

    {% menu 'meta' as meta_nav %}
    <nav>
    {% for p in meta_nav %}
        {% is_descendant_of page p include_self=True as active %}
        <a href="{{ p.get_absolute_url }}" {% if active %}class="active">
            {{ p.title }}
        </a>
    {% endfor %}
    </nav>

The menu is saved as ``menu`` on the model.


``TemplateMixin``
==================

It is sometimes useful to have different templates for CMS models such
as pages, articles or anything comparable. The ``TemplateMixin``
provides a ready-made solution for selecting django-content-editor_
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

The template key is stored as ``template_key`` on the model, the
``Template`` instance is available using the ``template`` property.
django-content-editor_ also requires a ``regions`` property for its
editing interface; the property returns the regions list from the
selected template.


``LanguageMixin``
=================

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
        page = # Fetch the Page instance somehow
        page.activate_language(request)

Note that this does not persist the language in the session or in a
cookie. If you need this, you should use Django's
``django.views.i18n.set_language`` view.


.. _django-content-editor: http://django-content-editor.readthedocs.org/
