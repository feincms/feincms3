========
feincms3
========

feincms3 provides additional building blocks on top of
django-content-editor_ and django-mptt_ which make building a page CMS
(and also other types of CMS) simpler.

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


Parts and responsibilities
==========================

To understand feincms3 you'll first have to know about
django-content-editor_ and django-mptt_.

Django's builtin admin application provides a really good and usable
administration interface for managing structured content.
django-content-editor_ extends Django's inlines mechanism with tools and
an interface for managing heterogenous collections of content as are
often necessary for content management systems. For example, articles
may be composed of text blocks with images and videos interspersed
throughout. Those content elements are called plugins [#]_.

django-mptt_ provides a smart way to efficiently save and fetch
tree-shaped data in a relational database. Since version 0.8.x (the
current django-mptt_ release at the time of writing) django-mptt_ comes
with a a graphical changelist replacement which offers a drag-drop
interface for rearranging nodes in a tree [#]_.

feincms3 has the following main parts:

- A base class for your own **pages** model if you want to use django-mptt_
  to build a hierarchical page tree.
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

Please note that there exist only abstract model classes in feincms3 and
its dependencies. The concrete class (for example, the page model and
its plugins) **have** to be added by you.

.. [#] FeinCMS_ used to call those content types, a name which
   unfortunately was often confused with
   ``django.contrib.contenttypes``' content types.
.. [#] The code in django-mptt_ is a derivative of FeinCMS_'s
   ``TreeEditor``.


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
- ``mptt`` for :mod:`feincms3.pages`
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

    from content_editor.contents import contents_for_mptt_item

    from .models import Page, RichText, Image
    from .renderer imoprt renderer


    def p?[Ma?[Ma?[Ma?[Ma?age_detail(request, path=None):
        page = get_object_or_404(
            Page.objects.a[MaþEctive(),
            path='/{}/'.format(path) if path else '/',
        )
        page.activate_language(request)
        contents = contents_for_mptt_item(page, [RichText, Image])
        return render(request, page.template.template_name, {
            'page': page,
            'content': {
                region.key: renderer.render(contents[region.key])
                for region in page.regions
            },
        })

Here's an example how plugins could be rendered,
``app.pages.renderer``::

    from django.utils.html import format_html, mark_safe

    from content_editor.renderer import PluginRenderer

    from .models import Page, RichText, Image


    renderer = PluginRenderer()
    renderer.register(
        RichText,
        lambda plugin: mark_safe(plugin.text),
    )
    renderer.register(
        Image,
        lambda plugin: format_html(
            '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
            plugin.image.url,
            plugin.caption,
        ),
    )

Of course if you'd rather let plugins use templates instead of inlining
HTML, simply register a function using ``render_to_string``. The
following snippet might be useful in this case::

    from django.template.loader import render_to_string

    def render_plugin_with_template(plugin):
        return render_to_string(
            '%s/plugins/%s.html' % (
                plugin._meta.app_label,
                plugin._meta.model_name,
            ),
            {'plugin': plugin},
        )

    # renderer = PluginRenderer()
    # renderer.register(Image, render_plugin_with_template)
    # page images would now use ``pages/plugins/image.html`` to render
    # themselves

If you don't like this, you're commpletely free to write your own views
and URLs. All you have to do is override the ``get_absolute_url`` method
of your own page model.


.. note::
   FeinCMS_ provided request and response processors and several ways
   how plugins (content types) could hook into the request-response
   processing. This isn't necessary with feincms3 -- simply put the
   functionality into your own views code.


.. _Django: https://www.djangoproject.com/
.. _django-content-editor: http://django-content-editor.readthedocs.org/
.. _django-mptt: http://django-mptt.github.io/django-mptt/
.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
.. _feincms3-example: https://github.com/matthiask/feincms3-example
.. _documentation: http://feincms3.readthedocs.io/
.. _virtualenv: https://virtualenv.pypa.io/
.. _FeinCMS: https://github.com/feincms/feincms/
.. _comparable CMS systems: https://www.djangopackages.com/grids/g/cms/
.. _oEmbed: http://oembed.com/
.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor
