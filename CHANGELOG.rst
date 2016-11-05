==========
Change log
==========

`Next version`_
~~~~~~~~~~~~~~~

- **BACKWARDS INCOMPATIBLE** Moved ``feincms3.plugins.versatileimage``
  into its own module, feincms3-images_, thereby removing the need to
  have to install django-versatileimagefield_ for feincms3.
- Fixed oEmbed read timeouts to not crash but retry after 60 seconds
  instead.
- Added the ``TemplatePluginRenderer.regions`` helper and the
  ``{% render_region %}`` template tag which support caching of plugins.
- Disallowed empty static paths for pages. ``Page.get_absolute_url()``
  fails with the recommended URL pattern when ``path`` equals ``''``.
- Added flake8_ and isort_ style checking.


`0.12`_ (2016-10-23)
~~~~~~~~~~~~~~~~~~~~

- Made ``reverse_any`` mention all viewnames in the ``NoReverseMatch``
  exception instead of bubbling the last viewname's exception.
- Added a ``RedirectMixin`` to ``feincms3.mixins`` for redirecting
  pages to other pages or arbitrary URLs.
- Added a footgun plugin (raw HTML code).
- Reinstate Python 2 compatibility because Python 2 still seems to be in
  wide use.


`0.11`_ (2016-09-19)
~~~~~~~~~~~~~~~~~~~~

- Changed the implementation of the ``is_descendant_of`` template tag do
  not depend on django-mptt_'s API anymore, and removed the
  compatibility shims from ``AbstractPage``.
- Made the documentation build again and added some documentation for
  the new ``feincms3.admin`` module.
- Made ``TreeAdmin.move_view`` run transactions on the correct database
  in multi-DB setups.
- Removed the unused ``NoCommitException`` class.
- Fixed a crash in the ``MoveForm`` validation.
- Made ``AppsMiddleware`` work with Django's ``MIDDLEWARE`` setting.
- Made the ``{% menu %}`` template tag not depend on a ``page`` variable
  in context.


`0.10`_ (2016-09-13)
~~~~~~~~~~~~~~~~~~~~

- **BACKWARDS INCOMPATIBLE** Switched from django-mptt_ to
  django-cte-forest_ which means that feincms3 is for the moment
  PostgreSQL_-only. By switching we completely avoid the MPTT attribute
  corruption which plagued projects for years. The `lft` attribute is
  directly reusable as `position`, and should be renamed in a migration
  insteaf of created from scratch to avoid losing the ordering of nodes
  within a branch.
- Added a ``feincms3.admin.TreeAdmin`` which shows the tree hierarchy
  and has facilities for moving nodes around.
- Avoided a deprecation warning on Django 1.10 regarding
  ``django.core.urlresolvers``.
- Started rolling releases using Travis CI's PyPI deployment provider.
- Made ``{% is_descendant_of %}`` return ``False`` if either of the
  variables passed is no page instance instead of crashing.


`0.9`_ (2016-08-17)
~~~~~~~~~~~~~~~~~~~

- Dropped compatibility with Python 2.
- Fixed ``AbstractPage.save()`` to actually detect page moves correctly
  again. Calling ``save()`` in a transaction was a bad idea because it
  messed with MPTT's bookkeeping information. Depending on the
  transaction isolation level going back to a clean slate *after*
  ``clean()`` proved much harder than expected.


`0.8`_ (2016-08-05)
~~~~~~~~~~~~~~~~~~~

- Added ``feincms3.apps.reverse_fallback`` to streamline reversing with
  fallback values in case of crashes.
- The default template renderer context
  (``TemplatePluginRenderer.register_template_renderer``) contains now the
  plugin instance as ``plugin`` instead of nothing.
- Make django-mptt-nomagic_ a required dependency, by depending on the fact
  that nomagic always calls ``Page.save()`` (django-mptt_ does not do that
  when nodes are moved using ``TreeManager.node_move``, which is used in the
  draggable mptt admin interface. Use a ``node_moved`` signal listener which
  calls ``save()`` if the ``node_moved`` call includes a ``position`` keyword
  argument if you can't switch to django-mptt-nomagic_ for some reason.


`0.7`_ (2016-07-21)
~~~~~~~~~~~~~~~~~~~

- Removed all dependencies from ``install_requires`` to make it easier
  to replace individual items.
- Enabled the use of ``i18n_patterns`` in ``ROOT_URLCONF`` by importing
  and adding the urlpatterns contained instead of ``include()``-ing the
  module in ``apps_urlconf``.
- Modified the cleansing configuration to allow empty ``<a>`` tags
  (mostly useful for internal anchors).
- Fixed crash when adding a page with a path that exists already (when
  not using a statich path).


`0.6`_ (2016-07-11)
~~~~~~~~~~~~~~~~~~~

- Updated the translation files.
- Fixed crashes when path of pages would not be unique when moving
  subtrees.


`0.5`_ (2016-07-07)
~~~~~~~~~~~~~~~~~~~

- Fixed a crash where apps without ``required_fields`` could not be
  saved.
- Added a template snippet based renderer for plugins.
- Prevented adding the exact same application (that is, the same
  ``app_instance_namespace``) more than once.


`0.4`_ (2016-07-04)
~~~~~~~~~~~~~~~~~~~

- Made application instances (``feincms3.apps``) more flexible by
  allowing programmatically generated instance namespace specifiers.


`0.3`_ (2016-07-02)
~~~~~~~~~~~~~~~~~~~

- Lots of work on the documentation.
- Moved all signal receivers into their classes as staticmethods.
- Fixed a crash on an attempted save of an ``External`` plugin instance
  with an empty URL.
- Added an incomplete testsuite, and add the Travis CI badge to the README.
- Removed the requirement of passing a context to ``render_list`` and
  ``render_detail``.


`0.2`_ (2016-06-28)
~~~~~~~~~~~~~~~~~~~

- The external plugin admin form now checks whether the URL can be
  embedded using OEmbed or not.
- Added the ``plugin_ckeditor.js`` file required for the rich text
  editor.
- Added a ``SnippetInline`` for consistency.
- Ensured that choice fields have a ``get_*_display`` method by setting
  dummy choices in advance (menus, snippets and templates).
- Added automatically built documentation on
  `readthedocs.io <http://feincms3.readthedocs.io/>`_.


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
.. _django-mptt-nomagic: https://github.com/django-mptt/django-mptt/pull/486
.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse
.. _feincms3-images: https://github.com/matthiask/feincms3-images/
.. _django-cte-forest: https://github.com/matthiask/django-cte-forest
.. _PostgreSQL: https://www.postgresql.org/
.. _flake8: https://pypi.python.org/pypi/flake8
.. _isort: https://pypi.python.org/pypi/isort

.. _0.1: https://github.com/matthiask/feincms3/commit/9f421bb48
.. _0.2: https://github.com/matthiask/feincms3/compare/0.1...0.2
.. _0.3: https://github.com/matthiask/feincms3/compare/0.2...0.3
.. _0.4: https://github.com/matthiask/feincms3/compare/0.3...0.4
.. _0.5: https://github.com/matthiask/feincms3/compare/0.4...0.5
.. _0.6: https://github.com/matthiask/feincms3/compare/0.5...0.6
.. _0.7: https://github.com/matthiask/feincms3/compare/0.6...0.7
.. _0.8: https://github.com/matthiask/feincms3/compare/0.7...0.8
.. _0.9: https://github.com/matthiask/feincms3/compare/0.8...0.9
.. _0.10: https://github.com/matthiask/feincms3/compare/0.9...0.10
.. _0.11: https://github.com/matthiask/feincms3/compare/0.10...0.11
.. _0.12: https://github.com/matthiask/feincms3/compare/0.11...0.12
.. _Next version: https://github.com/matthiask/feincms3/compare/0.12...master
