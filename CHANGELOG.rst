.. _changelog:

Change log
==========

`Next version`_
~~~~~~~~~~~~~~~

- Updated the Travis CI matrix to cover more versions of Django and
  Python while reducing the total job count to speed up builds.
- Made the default textarea used for editing the HTML plugin smaller.
- Added documentation for the new ``reenter`` subrenderer hook.
- Augmented the snippet plugin with a way to specify a template-specific
  plugin context callable.


`0.27`_ (2019-01-15)
~~~~~~~~~~~~~~~~~~~~

- Fixed the CKEditor plugin script to resize the widget to fit the width
  of the content editor area.
- Added configuration for easily running prettier and ESLint on the
  frontend code.
- Dropped Python 2 compatibility, again. The first attempt was made
  almost 30 months ago.
- Changed the subrenderer to use yielding instead of returning
  fragments.


`0.26`_ (2018-11-22)
~~~~~~~~~~~~~~~~~~~~

- Removed tree fields when loading applications.
- Stopped mentioning the ``AppsMixin`` in the reference documentation.
- Fixed a few typos and converted more string quotes in the docs.
- Changed the docs to use allow/deny instead of black/white.
- Changed ``feincms3.plugins`` do not hide import errors from our own
  modules anymore (again).
- Added a cloning functionality to copy the values of individual fields
  and also of the pages' content onto other pages.
- Fixed a problem where ``Snippet.__str__`` would unexpectedly (for
  Django) return lazy strings.
- Changed the type of ``RedirectMixin.redirect_to_page`` to
  ``TreeNodeForeignKey`` so that the hierarchy is shown in the dropdown.
- Added more careful detection of chain redirects and improved the error
  messages a bit.
- Made it clearer that ``AbstractPage.position``'s value should probably
  be greater than zero. Thanks to Hannah Cushman for the contribution!


`0.25`_ (2018-09-07)
~~~~~~~~~~~~~~~~~~~~

- **BACKWARDS INCOMPATIBLE** Removed the imports of plugins into
  ``feincms3.plugins``. Especially with the image plugins it could be
  non-obvious whether the plugin uses django-imagefield or
  django-versatileimagefield. Instead, the modules are imported so that
  classes and functions can be referenced using e.g.
  ``plugins.image.Image`` instead of ``plugins.Image`` as before.
- Moved the documentation from autodoc to a more guide-oriented format.
- Changed ``TemplatePluginRenderer.render_plugin_in_context`` to raise a
  specific ``PluginNotRegistered`` exception upon encountering
  unregistered plugins instead of a generic ``KeyError``.
- Made it possible to pass fixed strings (not callables) to
  ``TemplatePluginRenderer.register_string_renderer``.
- Added an incubator in ``feincms3.incubator`` for experimental modules
  with absolutely no compatibility guarantees.
- Changed the ``TreeAdmin.move_view`` to return a redirect to the admin
  index page instead of a 404 for missing nodes (as the Django admin's
  views also do since Django 1.11).
- Fixed an edge case in ``apps_urlconf`` which would generate a few
  nonsensical URLs if no language is activated currently.
- Made it an error to add redirects to a page which is already the
  target of a different redirect. Adding redirects to a page which
  itself already redirects was already an error.


`0.24`_ (2018-08-25)
~~~~~~~~~~~~~~~~~~~~

- Fixed one use of removed API.
- Fixed a bug where the move form "Save" button wasn't shown with Django
  2.1.
- Made overriding the ``Regions`` type used in
  ``TemplatePluginRenderer`` less verbose.
- Modified the documentation to produce several pages. Completed the
  guide for building your own CMS and added a section about customizing
  rendering using ``Regions`` subclasses.


`0.23`_ (2018-07-30)
~~~~~~~~~~~~~~~~~~~~

- Switched the preferred quote to ``"`` and started using `black
  <https://pypi.org/project/black/>`_ to automatically format Python
  code.

Switched to a new library for recursive common table expressions
----------------------------------------------------------------

django-tree-queries_ supports more database engines, which means that
the PostgreSQL_-only days of feincms3 are gone.

Incompatible differences are few:

- The attributes on page objects are named ``tree_depth`` and ``tree_path``
  now instead of ``depth`` and ``cte_path``. If you're using ``WHERE``
  clauses on your querysets change ``depth`` to ``__tree.tree_depth``
  (or only ``tree_depth``). Properties for backward compatibility have
  been added to the ``AbstractPage`` class, but of course those cannot
  be used in database queries.
- django-tree-queries_ uses the correct definition of node depth where
  root nodes have a depth of ``0``, not ``1``.
- django-tree-queries_ does not add the CTE by default to all queries,
  instead, users are expected to call ``.with_tree_fields()`` themselves
  if they want to use the CTE attributes. For the time being, the
  ``AbstractPageManager`` always returns querysets with tree fields.


`0.22`_ (2018-05-04)
~~~~~~~~~~~~~~~~~~~~

- Fixed a problem in ``MoveForm`` where invalid move targets would crash
  because of missing form fields to attach the error to instead of
  showing the underlying problem.
- Made it possible to override the list of apps processed in
  ``apps_urlconf``.
- Converted the apps middleware into a function, now named
  ``apps_middleware``. The old name ``AppsMiddleware`` will stay
  available for some undefined time.
- Made the path clash check less expensive by running less SQL queries.
- Made page saving a bit less expensive by only saving descendants when
  ``is_active`` or ``path`` changed.


`0.21`_ (2018-03-28)
~~~~~~~~~~~~~~~~~~~~

- Added a template tag for ``reverse_app``.
- **(At least a bit) BACKWARDS INCOMPATIBLE** Switched the preferred
  image field from django-versatileimagefield_ to django-imagefield_.
  The transition should mostly require replacing ``versatileimagefield``
  with ``imagefield`` in your settings etc., adding the appropriate
  ``IMAGEFIELD_FORMATS`` setting and running ``./manage.py
  process_imagefields`` once. Switch from ``feincms3[all]`` to
  ``feincms3[versatileimagefield]`` to stay with
  django-versatileimagefield_ for the moment.


`0.20`_ (2018-03-21)
~~~~~~~~~~~~~~~~~~~~

- Changed ``render_list`` and ``render_detail`` to return
  ``TemplateResponse`` instances instead of pre-rendered instances to
  increase the shortcuts' flexibility.
- Factored the JSON fetching from ``oembed_html`` into a new
  ``oembed_json`` helper.
- Added Django 2.0 to the Travis CI build (nothing had to be changed,
  0.19 was already compatible)
- Changed the ``TemplatePluginRenderer`` to also work when used
  standalone, not from inside a template.
- Dropped compatibility with Django versions older than 1.11.
- Changed ``AppsMixin.clean_fields`` to use ``_default_manager`` instead
  of ``_base_manager`` to search for already existing app instances.
- Changed the page move view to suppress the "Save and add another"
  button with great force.


`0.19`_ (2017-08-17)
~~~~~~~~~~~~~~~~~~~~

The diff for this release is big, but there are almost no changes in
functionality.

- Minor documentation edits, added a form builder example app to the
  documentation.
- Made ``reverse_fallback`` catch ``NoReverseMatch`` exceptions only,
  and fixed a related test which didn't reverse anything at all.
- Switch to tox_ for building docs, code style checking and local test
  running.
- Made the ``forms.Media`` CSS a list, not a set.


`0.18`_ (2017-05-10)
~~~~~~~~~~~~~~~~~~~~

- Slight improvements to ``TreeAdmin``'s alignment of box drawing characters.
- Allow overriding the outer namespace name used in ``feincms3.apps`` by
  setting the ``LANGUAGE_CODES_NAMESPACE`` class attribute of the pages
  class. The default value of ``language-codes`` has  been changed to
  ``apps``. Also, the outer instance namespaces of apps are now of the
  form ``<LANGUAGE_CODES_NAMESPACE>-<language_code>`` (example:
  ``apps-en`` for english), not only ``<language_code>``. This makes
  namespace collisions less of a concern.


`0.17.1`_ (2017-05-02)
~~~~~~~~~~~~~~~~~~~~~~

- Minor documentation edits.
- Added the ``AncestorFilter`` for filtering the admin changelist by
  ancestor. The default setting is to allow filtering by the first two
  tree levels.
- Switched from feincms-cleanse_ to html-sanitizer_ which allows
  configuring the allowed tags and attributes using a
  ``HTML_SANITIZERS`` setting.


`0.16`_ (2017-04-24)
~~~~~~~~~~~~~~~~~~~~

- Fixed the releasing-via-PyPI configuration.
- Removed strikethrough from our recommended rich text configuration,
  since feincms-cleanse_ would remove the tag anyway.
- Made ``TemplatePluginRenderer.regions`` and the ``Regions`` class into
  documented API.
- Made ``register_template_renderer``'s ``context`` argument default to
  ``default_context`` instead of ``None``, so please stop passing
  ``None`` and expecting the default context to work as before.
- Before adding Python 2 compatibility, a few methods and functions had
  keyword-only arguments. Python 2-compatible keyword-only enforcement
  has been added back to make it straightforward to transition back to
  keyword-only arguments later.


`0.15`_ (2017-04-05)
~~~~~~~~~~~~~~~~~~~~

- Dropped the ``is_descendant_of`` template tag. It was probably never
  used without ``include_self=True``, and this particular use case is
  better covered by checking whether a given primary key is a member
  of ``page.cte_path``.
- Dropped the ``menu`` template tag, and with it also the
  ``group_by_tree`` filter. Its arguments were interpreted according to
  the long-gone django-mptt_ and it promoted bad database querying
  patterns.
- Dropped the now-empty ``feincms3_pages`` template tag library.
- Added a default manager implementing ``active()`` to ``AbstractPage``.


`0.14`_ (2017-03-14)
~~~~~~~~~~~~~~~~~~~~

- Removed Django_ from ``install_requires`` so that updating
  feincms3 without updating Django is easier.
- Allowed overriding the Page queryset used in ``page_for_app_request``
  (for example for adding ``select_related``).
- Moved validation logic in varous model mixins from ``clean()`` to
  ``clean_fields(exclude)`` to be able to attach errors to individual
  form fields (if they are available on the given form).
- Added Django 1.11 to the build matrix on Travis CI.
- Fixed an "interesting" bug where the ``TreeAdmin`` would crash with
  an ``AttributeError`` if no query has been run on the model before.


`0.13`_ (2016-11-07)
~~~~~~~~~~~~~~~~~~~~

- Fixed oEmbed read timeouts to not crash but retry after 60 seconds
  instead.
- Added the ``TemplatePluginRenderer.regions`` helper and the
  ``{% render_region %}`` template tag which support caching of plugins.
- Disallowed empty static paths for pages. ``Page.get_absolute_url()``
  fails with the recommended URL pattern when ``path`` equals ``''``.
- Added flake8_ and isort_ style checking.
- Made the dependency on feincms-cleanse_, requests_ and
  django-versatileimagefield_ less strong than before. Plugins depending
  on those apps simply will not be available in the ``feincms3.plugins``
  namespace, but you have to be careful yourself to not import the
  actual modules yourself.
- Added Django_, django-content-editor_ and django-cte-forest_ to
  ``install_requires`` so that they are automatically installed, and
  added an extra with dependencies for all included plugins, so if you
  want that simply install ``feincms3[all]``.


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

- Changed the implementation of the ``is_descendant_of`` template tag to
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
  instead of created from scratch to avoid losing the ordering of nodes
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


.. _Django: https://www.djangoproject.com/
.. _django-ckeditor: https://github.com/django-ckeditor/django-ckeditor/
.. _django-content-editor: https://django-content-editor.readthedocs.io/
.. _django-cte-forest: https://django-cte-forest.readthedocs.io/
.. _django-imagefield: https://django-imagefield.readthedocs.io/
.. _django-mptt: https://django-mptt.readthedocs.io/
.. _django-mptt-nomagic: https://github.com/django-mptt/django-mptt/pull/486
.. _django-tree-queries: https://github.com/matthiask/django-tree-queries/
.. _django-versatileimagefield: https://django-versatileimagefield.readthedocs.io/
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse/
.. _html-sanitizer: https://pypi.python.org/pypi/html-sanitizer/
.. _PostgreSQL: https://www.postgresql.org/
.. _flake8: https://pypi.python.org/pypi/flake8
.. _isort: https://pypi.python.org/pypi/isort
.. _requests: http://docs.python-requests.org/
.. _tox: https://tox.readthedocs.io/

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
.. _0.13: https://github.com/matthiask/feincms3/compare/0.12...0.13
.. _0.14: https://github.com/matthiask/feincms3/compare/0.13...0.14
.. _0.15: https://github.com/matthiask/feincms3/compare/0.14...0.15
.. _0.16: https://github.com/matthiask/feincms3/compare/0.15...0.16
.. _0.17.1: https://github.com/matthiask/feincms3/compare/0.16...0.17.1
.. _0.18: https://github.com/matthiask/feincms3/compare/0.17.1...0.18
.. _0.19: https://github.com/matthiask/feincms3/compare/0.18...0.19
.. _0.20: https://github.com/matthiask/feincms3/compare/0.19...0.20
.. _0.21: https://github.com/matthiask/feincms3/compare/0.20...0.21
.. _0.22: https://github.com/matthiask/feincms3/compare/0.21...0.22
.. _0.23: https://github.com/matthiask/feincms3/compare/0.22...0.23
.. _0.24: https://github.com/matthiask/feincms3/compare/0.23...0.24
.. _0.25: https://github.com/matthiask/feincms3/compare/0.24...0.25
.. _0.26: https://github.com/matthiask/feincms3/compare/0.25...0.26
.. _0.27: https://github.com/matthiask/feincms3/compare/0.26...0.27
.. _Next version: https://github.com/matthiask/feincms3/compare/0.27...master
