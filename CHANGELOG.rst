==========
Change log
==========

`0.1`_ (Unreleased)
~~~~~~~~~~~~~~~~~~~

- Added plugins (apps, external, richtext, snippet and versatileimage)
  for use with `django-content-editor`_.
- Added cleansing
- Added shortcuts (``render_list`` and ``render_detail`` -- the most
  useful parts of Django's class based generic views)
- Added an abstract page base model building on `django-mptt`_ with
  mixins for handling templates and menus.
- Added template tags for fetching and grouping menu entries inside
  templates.

.. _django-content-editor: http://django-content-editor.readthedocs.org/en/latest/
.. _django-mptt: http://django-mptt.github.io/django-mptt/
