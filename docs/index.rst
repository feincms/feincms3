========
feincms3
========

Version |release|

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


Prerequisites and installation
==============================

feincms3 runs on Python 2.7 and Python 3.4 or better. The minimum
required Django version is 1.9 (because of django-content-editor_'s
dependency on Django's features that have only been added in this
version). Also, because of django-cte-forest_ it is currently
PostgreSQL_ only because it lacks support for other database engines'
recursive common table expressions (patches welcome!).

feincms3 should be installed using pip_. The default of ``pip install
feincms3`` depends on django-content-editor_ and django-cte-forest_
(explained below). By specifying ``pip install feincms3[all]`` instead
you can also install all optional dependencies (otherwise you'll not be
able to use the built-in rich text, image and oEmbed plugins).

.. note::
   This documentation uses Python 3's keyword-only syntax in a few
   places. Of course keyword-only arguments are only available with
   older Python versions, but you still cannot pass them as positional
   arguments or you'll get ``TypeError`` exceptions.


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

.. module:: feincms3.renderer

.. autoclass:: TemplatePluginRenderer
   :members:

.. autofunction:: default_context

.. autoclass:: Regions
   :members:


Shortcuts (``feincms3.shortcuts``)
==================================

.. automodule:: feincms3.shortcuts
   :members:


Template tags
=============

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
  as the page model, named ``app.pages`` in this guide.

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

    from .models import Page
    from .renderer import renderer


    def page_detail(request, path=None):
        page = get_object_or_404(
            Page.objects.active(),
            path='/{}/'.format(path) if path else '/',
        )
        page.activate_language(request)
        return render(request, page.template.template_name, {
            'page': page,
            'regions': renderer.regions(
                page,
                inherit_from=page.ancestors().reverse(),
            ),
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

And the associated template with downscaling of bigger images::

    <figure><img src="{{ plugin.image.thumbnail.400x400 }}" alt=""/></figure>

If you don't like this, you're completely free to write your own views,
URLs and ``get_absolute_url`` method.

.. note::
   FeinCMS_ provided request and response processors and several ways
   how plugins (content types) could hook into the request-response
   processing. This isn't necessary with feincms3 -- simply put the
   functionality into your own views code.

And a ``pages/standard.html`` template::

    {% extends "base.html" %}

    {% load feincms3_renderer %}

    {% block title %}{{ page.title }} - {{ block.super }}{% endblock %}

    {% block content %}
        <main>
            <h1>{{ page.title }}</h1>
            {% render_region regions "main" %}
            {# or maybe {% render_region regions "main" timeout=30 %} #}
        </main>
    {% endblock %}


Admin classes
~~~~~~~~~~~~~

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
        # tabbed fieldsets -- simply add 'tabbed' to the 'classes' key
        # the same way you'd add 'collapse'.

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


An example forms builder app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example app uses form_designer_ to provide a forms builder
integrated with the pages app described above. Apart from installing
form_designer_ itself the following steps are necessary:

- Add an entry to ``Page.APPLICATIONS`` for the forms app. The
  ``app_instance_namespace`` bit is not strictly necessary, but it might
  be helpful to reverse URLs where a specific form is integrated using
  ``reverse_app(('forms-%s' % form.pk,), 'form')``::

    # ...
    class Page(...):
        # ...
        APPLICATIONS = [
            ('forms', _('forms'), {
                'urlconf': 'app.forms',
                'app_instance_namespace': lambda page: '%s-%s' % (
                    page.application,
                    page.form_id,
                ),
                'required_fields': ('form',),
            }),
            # ...
        ]
        form = models.ForeignKey(
            'form_designer.Form',
            on_delete=models.SET_NULL,
            blank=True, null=True,
            verbose_name=_('form'),
        )

- Add the ``app/forms.py`` module itself::

    from django.conf.urls import url
    from django.http import HttpResponseRedirect
    from django.shortcuts import render

    from feincms3.apps import page_for_app_request

    from app.pages.renderer import renderer


    def form(request):
        page = page_for_app_request(request)
        page.activate_language(request)
        context = {}

        if 'ok' not in request.GET:
            form_class = page.form.form()

            if request.method == 'POST':
                form = form_class(request.POST)

                if form.is_valid():
                    # Discard return values from form processing.
                    page.form.process(form, request)
                    return HttpResponseRedirect('?ok')

            else:
                form = form_class()

            context['form'] = form

        context.update({
            'page': page,
            'regions': renderer.regions(
                page, inherit_from=page.ancestors().reverse()),
        })

        return render(request, 'form.html', context)


    app_name = 'forms'
    urlpatterns = [
        url(r'^$', form, name='form'),
    ]

- Add the required template::

    {% extends "base.html" %}

    {% load feincms3_renderer %}

    {% block content %}

    {% render_region regions 'main' timeout=15 %}

    {% if form %}
      <form method="post" action=".#form" id="form">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Submit</button>
      </form>
    {% else %}
      <h1>Thank you!</h1>
    {% endif %}
    {% endblock %}

Of course if you'd rather add another URL for the "thank you" page
you're free to add a second entry to the ``urlpatterns`` list and
redirect to this URL instead.


.. _Change log: https://github.com/matthiask/feincms3/blob/master/CHANGELOG.rst
.. _Django: https://www.djangoproject.com/
.. _FeinCMS: https://github.com/feincms/feincms/
.. _Noembed: https://noembed.com/
.. _comparable CMS systems: https://www.djangopackages.com/grids/g/cms/
.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor/
.. _django-content-editor: https://django-content-editor.readthedocs.io/
.. _django-cte-forest: https://django-cte-forest.readthedocs.io/
.. _django-mptt: https://django-mptt.readthedocs.io/
.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
.. _documentation: http://feincms3.readthedocs.io/
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse/
.. _feincms3-example: https://github.com/matthiask/feincms3-example/
.. _form_designer: https://pypi.python.org/pypi/form_designer/
.. _html-sanitizer: https://pypi.python.org/pypi/html-sanitizer/
.. _oEmbed: http://oembed.com/
.. _pip: https://pip.pypa.io/
.. _PostgreSQL: https://www.postgresql.org/
.. _requests: http://docs.python-requests.org/
.. _virtualenv: https://virtualenv.pypa.io/

.. include:: ../CHANGELOG.rst
