Introduction
============

Philosophy
~~~~~~~~~~

feincms3 follows the library-not-framework approach. Inversion of
control is avoided as much as possible, and great care is taken to
provide useful functionality which can still be easily replaced if
anyone wishes to do so.

Replacing functionality should not require using extension points or
configuration but simply different glue code, which should be short and
obvious enough to be repeated in different projects.

The idea is not necessarily to avoid code, but to avoid all sorts of
complexity, whether obvious or not. The cost of abstractions is that
there always comes a moment where you have understand the layers
beneath, and often the learning curve gets steep quickly.

feincms3 is your Do It Yourself kit for CMS building, as Django is your
Do It Yourself kit for website building.

feincms3 only has abstract model classes and mixins. Any concrete
classes (for example, the page model) **have** to be added by you in
your own project. This is by design, and paves the way for introducing
local customizations without having to rely on hooks, extension points
and whatnot.


Standing on the shoulders
~~~~~~~~~~~~~~~~~~~~~~~~~

Django's builtin admin application provides a really good and usable
administration interface for managing structured content.
django-content-editor_ extends Django's inlines mechanism with tools and
an interface for managing heterogenous collections of content as are
often necessary for content management systems. For example, articles
may be composed of text blocks with images and videos interspersed
throughout. Those content elements are called plugins.

django-tree-queries_ provides a smart way to efficiently fetch
tree-shaped data in a relational database supporting Common Table
Expressions.

.. note::
   What we are calling plugins is called a content type in FeinCMS_.
   This can be easily confused with Django's own contenttypes, therefore
   the name was changed for feincms3.

   Using django-mptt_ or other tree libraries is possible with feincms3
   as well if you don't want to use CTEs. Reimplementing the abstract
   page class with a different library should be straightforward.


The parts of feincms3
~~~~~~~~~~~~~~~~~~~~~

feincms3 has the following main parts:

- A base class for your own **pages** model if you want to use
  django-tree-queries_ to build a hierarchical page tree.
- Model **mixins** for common tasks such as building several navigation
  menus from a page tree, multilingual sites and selectable templates.
- A few ready-made **plugins** for rich text, images, oEmbed_ and template
  snippets.
- A HTML sanitization and **cleansing** function and a rich text widget
  building on html-sanitizer_ and django-ckeditor_.
- Facilities for embedding **apps** through the admin interface, such as
  any interactive content (forms) or apps with subpages (e.g. an
  articles app).
- A **renderer** and associated helpers and template tags.
- **admin** classes for visualizing and modifying the tree hierarchy.
- Various utilities (**shortcuts** and **template tags**).


.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor
.. _django-content-editor: https://django-content-editor.readthedocs.io
.. _django-mptt: https://django-mptt.readthedocs.io
.. _django-tree-queries: https://github.com/matthiask/django-tree-queries
.. _FeinCMS: https://github.com/feincms/feincms
.. _html-sanitizer: https://github.com/matthiask/html-sanitizer
.. _oEmbed: http://oembed.com
