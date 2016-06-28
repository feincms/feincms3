==========
Change log
==========

`0.2`_ (Unreleased)
~~~~~~~~~~~~~~~~~~~

- The external plugin admin form now checks whether the URL can be
  embedded using OEmbed or not.
- Added the ``plugin_ckeditor.js`` file required for the rich text
  editor.
- Added a ``SnippetInline`` for consistency.
- Ensured that choice fields have a ``get_*_display`` method by setting
  dummy choices in advance (menus, snippets and templates).


`0.1`_ (2016-06-25)
~~~~~~~~~~~~~~~~~~~

Added
-----

- Plugins (apps, external, richtext, snippet and versatileimage)
  for use with `django-content-editor`_.
- HTML editing and cleansing using `django-ckeditor`_ and
  `feincms-cleanse`_.
- Shortcuts (``render_list`` and ``render_detail`` -- the most
  useful parts of Django's class based generic views)
- An abstract page base model building on `django-mptt`_ with
  mixins for handling templates, menus and language codes.
- Template tags for fetching and grouping menu entries inside
  templates.
- A german translation.

Changed / Deprecated / Removed / Fixed / Security
-------------------------------------------------

- Nothing!


.. _django-ckeditor: https://pypi.python.org/pypi/django-ckeditor
.. _django-content-editor: http://django-content-editor.readthedocs.org/en/latest/
.. _django-mptt: http://django-mptt.github.io/django-mptt/
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse

.. _0.1: https://github.com/matthiask/feincms3/commit/9f421bb48
.. _0.2: https://github.com/matthiask/feincms3/compare/0.1...master
