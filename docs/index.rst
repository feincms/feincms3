========
feincms3
========

feincms3 provides additional building blocks on top of
django-content-editor_ and django-mptt_ which make building a page CMS
(and also other types of CMS) simpler.

This documentation consists of the following parts:

- First a short high-level overview explaining the various parts of
  feincms3 and the general rationale for yet another content management
  framework.
- Second a reference documentation which aims to explain the provided
  tools and modules in depth.

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

.. [#] FeinCMS_ used to call those content types, a name which
   unfortunately was often confused with
   ``django.contrib.contenttypes``' content types.
.. [#] The code in django-mptt_ is a derivative of FeincMS_'s
   ``TreeEditor``.


Pages base class
================

.. automodule:: feincms3.pages
.. autoclass:: feincms3.pages.AbstractPage


Mixins
======

.. automodule:: feincms3.mixins
.. autoclass:: feincms3.mixins.MenuMixin
.. autoclass:: feincms3.mixins.TemplateMixin
.. autoclass:: feincms3.mixins.LanguageMixin


Plugins
=======

All documented plugin classes and functions can be imported from
``feincms3.plugins`` as well.


External
~~~~~~~~

.. automodule:: feincms3.plugins.external
.. autofunction:: feincms3.plugins.external.oembed_html
.. autofunction:: feincms3.plugins.external.render_external
.. autoclass:: feincms3.plugins.external.External
.. autoclass:: feincms3.plugins.external.ExternalInline


Rich text
~~~~~~~~~

.. automodule:: feincms3.plugins.richtext
.. autoclass:: feincms3.plugins.richtext.RichText
.. autoclass:: feincms3.plugins.richtext.RichTextInline


Snippets
~~~~~~~~

.. automodule:: feincms3.plugins.snippet
.. autofunction:: feincms3.plugins.snippet.render_snippet
.. autoclass:: feincms3.plugins.snippet.Snippet
.. autoclass:: feincms3.plugins.snippet.SnippetInline


Versatile images
~~~~~~~~~~~~~~~~

This plugin uses django-versatileimagefield_ to do the heavy lifting.

.. automodule:: feincms3.plugins.versatileimage
.. autoclass:: feincms3.plugins.versatileimage.Image
.. autoclass:: feincms3.plugins.versatileimage.ImageInline


HTML cleansing
==============

HTML cleansing is by no means only useful for user generated content.
Managers also copy-paste content from word processing programs, the rich
text editor's output isn't always (almost never) in the shape we want it
to be, and a strict white-list based HTML sanitizer is the best answer
I have.

.. automodule:: feincms3.cleanse
.. autofunction:: feincms3.cleanse.cleanse_html
.. autoclass:: feincms3.cleanse.CleansedRichTextField


Apps
====

.. automodule:: feincms3.apps
.. autofunction:: feincms3.apps.reverse_any
.. autofunction:: feincms3.apps.reverse_app
.. autofunction:: feincms3.apps.apps_urlconf
.. autofunction:: feincms3.apps.page_for_app_request
.. autoclass:: feincms3.apps.AppsMiddleware
.. autoclass:: feincms3.apps.AppsMixin


Shortcuts
=========

.. automodule:: feincms3.shortcuts
.. autofunction:: feincms3.shortcuts.template_name
.. autofunction:: feincms3.shortcuts.render_list
.. autofunction:: feincms3.shortcuts.render_detail


Template tags
=============

.. automodule:: feincms3.templatetags.feincms3_pages
.. autofunction:: feincms3.templatetags.feincms3_pages.group_by_tree
.. autofunction:: feincms3.templatetags.feincms3_pages.is_descendant_of
.. autofunction:: feincms3.templatetags.feincms3_pages.menu


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
