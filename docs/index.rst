.. feincms3 documentation master file, created by
   sphinx-quickstart on Tue Jun 28 13:07:10 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to feincms3's documentation!
====================================

Contents:

.. toctree::
   :maxdepth: 2


Apps
====

.. automodule:: feincms3.apps
.. autofunction:: feincms3.apps.reverse_any
.. autofunction:: feincms3.apps.reverse_app
.. autofunction:: feincms3.apps.apps_urlconf
.. autofunction:: feincms3.apps.page_for_app_request
.. autoclass:: feincms3.apps.AppsMiddleware
.. autoclass:: feincms3.apps.AppsMixin


HTML cleansing
==============

.. automodule:: feincms3.cleanse
.. autofunction:: feincms3.cleanse.cleanse_html
.. autoclass:: feincms3.cleanse.CleansedRichTextField


Mixins
======

.. automodule:: feincms3.mixins
.. autoclass:: feincms3.mixins.MenuMixin
.. autoclass:: feincms3.mixins.TemplateMixin
.. autoclass:: feincms3.mixins.LanguageMixin


Pages base class
================

.. automodule:: feincms3.pages
.. autoclass:: feincms3.pages.AbstractPage


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


Plugins
=======

All documented plugin classes and methods can be imported from
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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
