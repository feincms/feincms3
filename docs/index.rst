========
feincms3
========

Version |release|

feincms3 offers tools and building blocks which make building a CMS that
is versatile, powerful and tailor-made at the same time for each project
a reachable reality.

It builds on other powerful tools such as Django itself and its
excellent standard admin interface, `django-content-editor
<https://django-content-editor.readthedocs.io>`__ to allow creating and
editing structured content and `django-tree-queries
<https://github.com/matthiask/django-tree-queries>`__ for querying
hierarchical data such as page trees.

The tools can be used for a page CMS, but also work well for other types
of content such as news magazines or API backends for mobile apps.


First steps
===========

Start here if you want to know what feincms3 is and build your first CMS
based on feincms3.

.. toctree::

   introduction
   installation
   build-your-cms


Guides
======

These guides discuss key concepts and show how to approach common tasks.
They do not have to be read in order and in general only build on the
knowledge imparted in :ref:`build-your-cms`.

.. toctree::

   guides/plugins
   guides/templates-and-regions
   guides/redirects
   guides/navigation
   guides/rendering
   guides/cookie-control
   guides/multilingual-sites
   guides/meta-opengraph-tags
   guides/multisite
   guides/multisite-custom
   guides/urls-and-views


Embedding apps
==============

feincms3 allows content managers to freely place pre-defined
applications in the page tree. Examples for apps include forms, or a
news app with archives, detail pages etc.

The apps documentation is meant to be read in order.

.. toctree::

   guides/apps-introduction
   guides/apps-form-builder
   guides/apps-and-instances


Reference
=========

.. toctree::
   :glob:

   ref/*


Project links
=============

.. toctree::

   project/changelog
   project/contributing


Related projects
================

* `feincms3-example <https://github.com/matthiask/feincms3-example>`_:
  Example project demonstrating some of feincms3's capabilities.
* `feincms3-sites <https://github.com/matthiask/feincms3-sites>`_:
  Multisite support for feincms3. Allows running a feincms3 site on
  several domains with separate page trees.
* `feincms3-downloads
  <https://github.com/matthiask/feincms3-downloads>`_: A downloads
  plugin which also supports thumbnailing e.g. PDFs using `ImageMagick
  <https://www.imagemagick.org/>`_.
* `feincms3-meta <https://github.com/matthiask/feincms3-meta>`_: Helpers
  and feincms3 mixins for making Open Graph tags and meta tags less
  annoying.
* `feincms3-forms <https://github.com/matthiask/feincms3-forms/>`_: A form
  builder using django-content-editor under the hood.
* `django-cabinet <https://github.com/matthiask/django-cabinet>`_: A
  media library for Django which works well with feincms3 and follows
  the same software design guidelines.
* `django-content-editor
  <https://django-content-editor.readthedocs.io>`_: The admin
  interface for editing structured heterogenous content.
* `django-imagefield <https://github.com/matthiask/django-imagefield>`_:
  An image field with in-depth image file validation and thumbnailing
  support which does not depend on a cache to be and stay fast.
* `django-sitemaps <https://github.com/matthiask/django-sitemaps>`_:
  Sitemaps generation using a real XML library and support for
  alternates.
* `django-tree-queries
  <https://github.com/matthiask/django-tree-queries>`_: The library
  feincms3's pages use for querying tree-shaped data.
* `html-sanitizer <https://github.com/matthiask/html-sanitizer>`_:
  Allowlist-based HTML sanitizer used for feincms3' rich text plugin.
* `FeinCMS <https://github.com/feincms/feincms>`__: First version.
