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
building (if you didn't want that you'd probably not be using Django
anyway).


Parts and responsibilities
~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's builtin admin application provides a really good and usable
administration interface for managing structured content.
django-content-editor_ extends Django's inlines mechanism with tools and
an interface for managing heterogenous collections of content as are
often necessary for content management systems. For example, articles
may be composed of text blocks with images and videos interspersed
throughout. Those content elements are called plugins [#]_.

django-tree-queries_ provides a smart way to efficiently fetch
tree-shaped data in a relational database supporting Common Table
Expressions [#]_.

feincms3 has the following main parts:

- A base class for your own **pages** model if you want to use
  django-tree-queries_ to build a hierarchical page tree.
- Model **mixins** for common tasks such as building navigation menus from a
  page tree, multilingual sites and sites with differing templates on
  different parts of the site.
- A few ready-made **plugins** for rich text, images, oEmbed_ and template
  snippets.
- A HTML sanitization and **cleansing** function and a rich text widget
  building on html-sanitizer_ and django-ckeditor_ which always cleanses
  the HTML entered.
- Facilities for embedding **apps** (i.e. a weblog, a contact form, ...)
  through the CMS.
- A **renderer** and associated template tags.
- **admin** classes for visualizing and modifying the tree hierarchy.
- Various utilities (**shortcuts** and **template tags**).

Please note that there exist only abstract model classes in feincms3 and
its dependencies. The concrete class (for example, the page model and
its plugins) **have** to be added by you. This is by design.

.. [#] FeinCMS_ used to call those content types, a name which
   unfortunately was often confused with
   ``django.contrib.contenttypes``' content types.
.. [#] Previously, feincms3 built on top of django-mptt_ and its
   ``DraggableMPTTAdmin``, a derivative of FeinCMS_'s ``TreeEditor``. This
   was dropped to completely avoid the tree corruption which plagued
   projects for years.


.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor
.. _django-content-editor: https://django-content-editor.readthedocs.io
.. _django-mptt: https://django-mptt.readthedocs.io
.. _django-tree-queries: https://github.com/matthiask/django-tree-queries
.. _FeinCMS: https://github.com/feincms/feincms
.. _html-sanitizer: https://github.com/matthiask/html-sanitizer
.. _oEmbed: http://oembed.com
