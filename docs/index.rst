========
feincms3
========

Version |release|

feincms3 provides additional building blocks on top of
django-content-editor_ and django-tree-queries_ which make building a page
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

The :ref:`changelog` should also be mentioned here because, while feincms3
is used in production on several sites and backwards incompatibility
isn't broken lightly, it still is a moving target.


Table of Contents
=================

.. toctree::
   :maxdepth: 2

   introduction
   installation
   pages
   mixins
   plugins
   cleansing
   apps
   renderer
   shortcuts
   admin
   next-steps
   changelog

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
