========
feincms3
========

feincms3 provides additional building blocks on top of
django-content-editor_ and django-cte-forest_ which make building a page
CMS (and also other types of CMS) simpler.

This documentation consists of the following parts:

- A short high-level overview explaining the various parts of feincms3
  and the general rationale for yet another content management
  framework.
- A reference documentation which aims to explain the provided tools and
  modules in depth.
- Next steps.

Now is also a good time to point out the example project
feincms3-example_. You should be able to setup a fully working
multilingual CMS including a hierarchical pages app and a blog app in
only a few easy steps (as long as you have the necessary build tools and
development libraries to setup the Python virtualenv_ and all its
dependencies).

The `Change log`_ should also be mentioned here because, while feincms3
is used in production on several sites and backwards incompatibility
isn't broken lightly, it still is a moving target.


Introduction
============

feincms3 follows the library-not-framework approach. Inversion of
control is avoided as much as possible, and great care is taken to
provide useful functionality which can still be easily replaced if
anyone wishes to do so.

Replacing functionality should not require using extension points or
configuration but simply different glue code, which should be short and
obvious enough to be repeated in different projects.

The idea is not necessarily to avoid code, but to avoid all sorts of
complexity, whether obvious or not. Abstractions fall down as soon as
they try to hide too much. feincms3 is your Do It Yourself kit for CMS
building (if you didn't want that you'd probably not be using Django_
anyway).


Installation
============

feincms3 should be installed using pip_. The default of ``pip install
feincms3`` depends on django-content-editor_ and django-cte-forest_
(explained below). By specifying ``pip install feincms3[all]`` instead
you can also install all optional dependencies (otherwise you'll not be
able to use the built-in rich text, image and oEmbed plugins).


Parts and responsibilities
==========================

To understand feincms3 you'll first have to know about
django-content-editor_ and django-cte-forest_.

Django's builtin admin application provides a really good and usable
administration interface for managing structured content.
django-content-editor_ extends Django's inlines mechanism with tools and
an interface for managing heterogenous collections of content as are
often necessary for content management systems. For example, articles
may be composed of text blocks with images and videos interspersed
throughout. Those content elements are called plugins [#]_.

django-cte-forest_ provides a smart way to efficiently fetch
tree-shaped data in a relational database supporting Common Table
Expressions [#]_.

feincms3 has the following main parts:

- A base class for your own **pages** model if you want to use
  django-cte-forest_ to build a hierarchical page tree.
- Model **mixins** for common tasks such as building navigation menus from a
  page tree, multilingual sites and sites with differing templates on
  different parts of the site.
- A few ready-made **plugins** for rich text, images, oEmbed_ and template
  snippets.
- A HTML sanitization and **cleansing** function and a rich text widget
  building on django-ckeditor_ which always cleanses the HTML entered.
- Facilities for embedding **apps** (i.e. a weblog, a contact form, ...)
  through the CMS.
- Various utilities (**shortcuts** and **template tags**).
- A **renderer** and associated template tags if you don't want to use
  django-content-editor_'s ``PluginRenderer``.
- A **admin** class for show the tree hierarchy with helpers for moving
  nodes to other places in the forest.

Please note that there exist only abstract model classes in feincms3 and
its dependencies. The concrete class (for example, the page model and
its plugins) **have** to be added by you.

.. [#] FeinCMS_ used to call those content types, a name which
   unfortunately was often confused with
   ``django.contrib.contenttypes``' content types.
.. [#] Previously, feincms3 built on top of django-mptt_ and its
   ``DraggableMPTTAdmin``, a derivative of FeinCMS_'s ``TreeEditor``. This
   was dropped to completely avoid the tree corruption which plagued
   projects for years.


Pages (``feincms3.pages``)
==========================

.. automodule:: feincms3.pages
   :members:


Mixins (``feincms3.mixins``)
============================

.. automodule:: feincms3.mixins
   :members:


Plugins (``feincms3.plugins``)
==============================

All documented plugin classes and functions can be imported from
``feincms3.plugins`` as well.


External
~~~~~~~~

.. automodule:: feincms3.plugins.external
   :members:


HTML
~~~~

.. automodule:: feincms3.plugins.html
   :members:


Rich text
~~~~~~~~~

.. automodule:: feincms3.plugins.richtext
   :members:


Snippets
~~~~~~~~

.. automodule:: feincms3.plugins.snippet
   :members:


Versatile images
~~~~~~~~~~~~~~~~

.. automodule:: feincms3.plugins.versatileimage
   :members:


HTML cleansing (``feincms3.cleanse``)
=====================================

.. automodule:: feincms3.cleanse
   :members:


Apps (``feincms3.apps``)
========================

.. automodule:: feincms3.apps
   :members:


Renderer (``feincms3.renderer``)
================================

.. automodule:: feincms3.renderer
   :members:


Shortcuts (``feincms3.shortcuts``)
==================================

.. automodule:: feincms3.shortcuts
   :members:


Template tags
=============

``feincms3_pages``
~~~~~~~~~~~~~~~~~~

.. automodule:: feincms3.templatetags.feincms3_pages
   :members:


``feincms3_renderer``
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: feincms3.templatetags.feincms3_renderer
   :members:


Admin classes (``feincms3.admin``)
==================================

.. automodule:: feincms3.admin
   :members:


Next steps
==========

To build a CMS you still need to write your URLconf and views, and add
settings to your Django project. As I already wrote at the beginning of
this guide, the feincms3-example_ project shows how everything works
together. Still, a few pointers follow:


Settings
~~~~~~~~

There are quite a few settings involved:

You'll have to add at least the following apps to ``INSTALLED_APPS``:

- ``feincms3``
- ``content_editor``
- ``ckeditor`` if you want to use :mod:`feincms3.plugins.richtext`
- ``versatileimagefield`` for :mod:`feincms3.plugins.versatileimage`
- ... and of course also the app where you put your concrete models such
  as the page model

If you're using the rich text plugin it is very much recommended to add
a ``CKEDITOR_CONFIGS`` setting as documented in :mod:`feincms3.cleanse`.


Views and URLs
~~~~~~~~~~~~~~

You're completely free to define your own views and URLs. That being
said, the ``AbstractPage`` class already has a ``get_absolute_url``
implementation which expects something like this::

    from django.conf.urls import url

    from app.pages import views


    app_name = 'pages'
    urlpatterns = [
        url(r'^(?P<path>[-\w/]+)/$', views.page_detail, name='page'),
        url(r'^$', views.page_detail, name='root'),
    ]

Where ``app.pages.views`` contains the following view::

    from django.shortcuts import get_object_or_404, render

    from content_editor.contents import contents_for_item

    from .models import Page
    from .renderer import renderer


    def page_detail(request, path=None):
        page = get_object_or_404(
            Page.objects.a[MaþEctive(),
            path='/{}/'.format(path) if path else '/',
        )
        page.activate_language(request)
        return render(request, page.template.template_name, {
            'page': page,
            'regions': renderer.regions(
                page, inherit_from=page.ancestors().reverse()),
        })

Here's an example how plugins could be rendered,
``app.pages.renderer``::

    from django.utils.html import format_html, mark_safe

    from feincms3.renderer import TemplatePluginRenderer

    from .models import Page, RichText, Image


    renderer = TemplatePluginRenderer()
    renderer.register_string_renderer(
        RichText,
        lambda plugin: mark_safe(plugin.text),
    )
    renderer.register_string_renderer(
        Image,
        lambda plugin: format_html(
            '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
            plugin.image.url,
            plugin.caption,
        ),
    )

Of course if you'd rather let plugins use templates, do this::

    renderer.register_template_renderer(
        Image,
        'plugins/image.html',
    )

And the associated template::

    <figure><img src="{{ plugin.image.url }}" alt=""/></figure>

If you don't like this, you're commpletely free to write your own views
and URLs. All you have to do is override the ``get_absolute_url`` method
of your own page model.


.. note::
   FeinCMS_ provided request and response processors and several ways
   how plugins (content types) could hook into the request-response
   processing. This isn't necessary with feincms3 -- simply put the
   functionality into your own views code.


For completeness, here's an example how the ``app.pages.admin`` module
might look like::

    from django.contrib import admin

    from content_editor.admin import ContentEditor
    from feincms3.admin import TreeAdmin
    from feincms3 import plugins

    from app.pages import models


    class PageAdmin(ContentEditor, TreeAdmin):
        list_display = (
            'indented_title', 'move_column', 'is_active',
            'menu', 'template_key', 'language_code', 'application')
        list_per_page = 250
        prepopulated_fields = {'slug': ('title',)}
        raw_id_fields = ('parent',)

        # fieldsets = ... (Recommended! No example here though. Note
        # that the content editor not only allows collapsed, but also
        # tabbed fieldsets -- simply add 'tabbed' to the 'classes' key.

        inlines = [
            plugins.RichTextInline.create(
                models.RichText,
            ),
            plugins.ImageInline.create(
                models.Image,
            ),
        ]

        # class Media: ... (Add font-awesome from a CDN and nicely
        # looking buttons for plugins as is described in
        # django-content-editor's documentation -- search for
        # "plugin_buttons.js")


    admin.site.register(models.Page, PageAdmin)

And a ``pages/standard.html`` template::

    {% extends "base.html" %}

    {% load feincms3_renderer %}

    {% block content %}
        <main>
            <h1>{{ page.title }}</h1>
            {% render_region regions "main" %}
            {# or maybe {% render_region regions "main" timeout=30 %} #}
        </main>
    {% endblock %}


.. _Change log: https://github.com/matthiask/feincms3/blob/master/CHANGELOG.rst
.. _Django: https://www.djangoproject.com/
.. _FeinCMS: https://github.com/feincms/feincms/
.. _comparable CMS systems: https://www.djangopackages.com/grids/g/cms/
.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor
.. _django-content-editor: http://django-content-editor.readthedocs.org/
.. _django-cte-forest: https://github.com/matthiask/django-cte-forest
.. _django-mptt: http://django-mptt.github.io/django-mptt/
.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
.. _documentation: http://feincms3.readthedocs.io/
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse
.. _feincms3-example: https://github.com/matthiask/feincms3-example
.. _oEmbed: http://oembed.com/
.. _pip: https://pip.pypa.io/
.. _requests: http://docs.python-requests.org
.. _virtualenv: https://virtualenv.pypa.io/
