========
feincms3
========

Version |release|

feincms3 provides additional building blocks on top of
django-content-editor_ and django-tree-queries_ which make building a page
CMS (and also other types of CMS) simpler.

.. note::

   Despite its version number feincms3 is already used in production on
   many sites and backwards compatibility isn't broken lightly.


User guide
==========

.. toctree::
   :maxdepth: 2

   introduction
   installation
   build-your-cms


Reference
=========

.. toctree::
   :maxdepth: 2

   pages
   mixins
   plugins
   cleansing
   apps
   renderer
   shortcuts
   admin
   changelog


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
  <https://github.com/matthiask/django-content-editor>`_: The admin
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


.. _Django: https://www.djangoproject.com/
.. _FeinCMS: https://github.com/feincms/feincms/
.. _Noembed: https://noembed.com/
.. _comparable CMS systems: https://www.djangopackages.com/grids/g/cms/
.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor/
.. _django-content-editor: https://django-content-editor.readthedocs.io/
.. _django-tree-queries: https://github.com/matthiask/django-tree-queries/
.. _django-imagefield: https://django-imagefield.readthedocs.io/
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
