========
feincms3
========

Version |release|

feincms3 provides additional building blocks on top of
`django-content-editor <https://django-content-editor.readthedocs.io>`_
and `django-tree-queries
<https://github.com/matthiask/django-tree-queries>`_ which make building
a page CMS (and also other types of CMS) simpler.

.. note::

   Despite its version number feincms3 is already used in production on
   many sites and backwards compatibility isn't broken lightly.

.. note::
   This documentation uses Python 3's keyword-only syntax in a few
   places. Python 2 does not support keyword-only arguments, but keyword
   usage is still enforced in feincms3.


First steps
===========

Start here if you want to know what feincms3 is and build your first CMS
based on feincms3.

.. toctree::
   :maxdepth: 2

   introduction
   installation
   build-your-cms


Guides
======

These guides discuss key concepts and show how to solve common problems.
They do not have to be read in order and in general only build on the
knowledge imparted in :ref:`build-your-cms`.

.. toctree::
   :maxdepth: 2

   guides/templates-and-regions
   guides/meta-opengraph-tags
   guides/multilingual-sites
   guides/navigation
   guides/form-builder-app
   guides/apps-and-instances
   guides/rendering
   guides/multisite


Reference
=========

.. toctree::
   :maxdepth: 1

   ref/pages
   ref/mixins
   ref/plugins
   ref/cleansing
   ref/apps
   ref/renderer
   ref/shortcuts
   ref/admin


Project links
=============

* `CHANGELOG
  <https://github.com/matthiask/feincms3/blob/master/CHANGELOG.rst>`__


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
