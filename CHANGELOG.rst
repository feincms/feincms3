.. _changelog:

Change log
==========

`Next version`_
~~~~~~~~~~~~~~~


`0.90b14`_ (2021-04-08)
~~~~~~~~~~~~~~~~~~~~~~~

This release contains a few backwards-incompatible changes which are the result
of efforts to produce a better foundation and fix oversights towards a 1.0
release of feincms3.

Page types
----------

Introduced the concept of page types. Merged the functionality of
``TemplateMixin`` and ``AppsMixin`` into a new ``PageTypeMixin`` and removed
``AppsMixin``.  Editors do not have to choose a template anymore when
activating an app. The latter overrides the former selection anyway. Also, this
allows using a custom selection of regions per application.

The following steps should be followed to upgrade existing sites:

- Create an automatic migration for the pages app.
- Edit the generated migration; create the ``page_type`` field first, and
  insert a ``RunSQL`` migration with the following SQL next: ``UPDATE
  pages_page SET page_type=CASE WHEN application<>'' THEN application ELSE
  template_key END``.
- Ensure that the ``app_instance_namespace`` is renamed to ``app_namespace``
  using a ``RenameField`` operation.
- Remove ``template_key`` from any code and replace ``application`` with
  ``page_type`` in the model admin configuration.
- Convert the entries in your ``TEMPLATES`` list to ``TemplateType`` instances,
  convert ``APPLICATIONS`` to ``ApplicationType`` instances and add both to a
  new ``TYPES`` class-level list. Note that those applications do not have
  *any* regions by default at all.
- The ``.template`` attribute of page classes does not exist any longer, to
  access e.g. the ``template_name`` replace ``page.template.template_name``
  with ``page.type.template_name``.
- Replace uses of ``page.application`` with ``page.page_type``,
  ``page.app_instance_namespace`` with ``page.app_namespace``. Properties
  mapping the former to the latter will stay in place for a release or two but
  they are already deprecated.

Other backwards-incompatible changes
------------------------------------

- Added ``alternative_text`` and ``caption`` fields to the image and the
  external plugin. Made both plugins prefer the caption in ``__str__``.
- Dropped the django-versatileimagefield-based image plugin.
- Removed the shims in ``feincms3.apps``.
- Standardized ``max_length`` values of ``CharField`` instances.
- Changed the snippet plugin to no longer try to render templates not in the
  ``TEMPLATES`` list. This means that you can just remove templates from
  ``TEMPLATES`` and not worry about database contents referencing templates
  which could have been removed in the meantime in the base case.

Minor changes
-------------

- Tried out a web-based translation platform. It wasn't exactly a big
  success, but we gained a few translations. Thanks to all contributors!
- Added a system check for page subclasses without the appropriate
  ordering definition.
- Changed the docs so that ``AbstractPage`` always comes before mixins
  so that ``AbstractPage``'s ``Meta`` properties are actually inherited
  by default.
- Changed the docs to recommend ``HttpResponseRedirect`` for the
  :class:`feincms3.mixins.RedirectMixin` redirect, not the ``redirect``
  shortcut. The latter may crash if the ``redirect_to_url`` doesn't look
  like a URL.
- Removed useless fallbacks.
- Fixed background colors in the move form to work with Django admin's dark
  mode.
- Added a ``feincms3/static-path-style.js`` script which automatically reduces
  the opacity of the path field unless the path is defined manually.
- Introduced an experimental inline CKEditor field.


`0.41`_ (2020-11-28)
~~~~~~~~~~~~~~~~~~~~

- Switched from Travis CI to GitHub Actions.
- Dropped the custom CKEditor activation JavaScript,
  `django-ckeditor`_ does all we need already.


`0.40`_ (2020-09-30)
~~~~~~~~~~~~~~~~~~~~

- Changed the move form styling (hide the radio inputs and use
  background colors, stripes to visualize the tree structure better.
- Added a warning when trying to move a node but there are no valid
  targets.
- Fixed the move form widget in the responsive layout.
- Avoided removing the parent node from the move form when moving the
  first child.
- Added a ``get_redirect_url`` to the
  :class:`~feincms3.mixins.RedirectMixin` which returns the target URL
  or ``None``.
- Added the :func:`feincms3.utils.is_first_party_link` utilty.


`0.39`_ (2020-09-25)
~~~~~~~~~~~~~~~~~~~~

- **BACKWARDS INCOMPATIBLE**: ``AbstractPageManager`` has been removed.
  You should subclass the :class:`feincms3.pages.AbstractPageQuerySet`
  instead and use the queryset's ``.as_manager(with_tree_fields=True)``
  classmethod to generate a manager which adds tree fields to select
  queries by default. If you didn't use the ``AbstractPageManager`` in
  your code directly you don't have to do anything.
- Started requiring ``django-tree-queries>=0.4.1``.
- Completely reworked the page move form; allow directly specifying the
  new position.


`0.38.1`_ (2020-09-23)
~~~~~~~~~~~~~~~~~~~~~~

- The ``AbstractPageManager.active()`` method has been moved to a new
  :class:`feincms3.pages.AbstractPageQuerySet`. If subclassing the
  queryset you should re-create the page manager using
  ``pages.AbstractPageManager.from_queryset(<your new subclass>)``.
- Made :func:`~feincms3.renderer.render_in_context` create its own
  ``Context`` if the context passed is ``None``.


`0.37`_ (2020-09-10)
~~~~~~~~~~~~~~~~~~~~

- Changed :func:`feincms3.applications.page_for_app_request` to only use
  active pages by default. This change should mostly not change anything
  since :func:`~feincms3.applications.apps_urlconf()` and therefore
  :func:`~feincms3.applications.apps_middleware` only add active
  applications anyway.
- Upgraded prettier and ESLint to recent versions.
- Added some code to embed videos from YouTube and Vimeo without
  requiring oEmbed.
- Dropped compatibility with Python 3.5.


`0.36`_ (2020-08-07)
~~~~~~~~~~~~~~~~~~~~

- Switched from ``url()`` to ``re_path()`` in ``apps_urlconf()`` to
  avoid deprecation warnings.
- Removed the limitation that apps could not have descendants in a page
  tree. There may be valid use cases for this, especially if an apps'
  URLconf module does not handle *all* paths.


`0.35`_ (2020-07-28)
~~~~~~~~~~~~~~~~~~~~

- **(not yet) BACKWARDS INCOMPATIBLE** Moved the ``feincms3.apps``
  module to :mod:`feincms3.applications`. The reason for this change is
  that Django 3.2 will start autodiscovering app configs and therefore
  automatically loads the ``.apps`` submodule of all entries in
  ``INSTALLED_APPS``. This leads to a crash when the ``.apps`` module
  contains models (such as our ``AppsMixin``). ``feincms3.apps`` isn't
  populated from Django 3.2 upwards because of this.
- Fixed an infinite recursion crash when referencing pages using
  ``on_delete=SET_NULL``
- Added a ``LanguageAndTranslationOfMixin`` which not only allows
  defining the language of objects but also defining objects to be
  translations of other objects.
- Added a ``|translations`` filter to the template tag library. Added a
  section about generating a language selector containing deep links to
  the :ref:`multilingual sites guide <multilingual-sites>` guide.
- Added Travis CI jobs for Django 3.1b1 and Python 3.8.
- Renamed the main branch to ``main``.
- Removed all arguments to ``super()`` since we're Python 3-only.
- Dropped workarounds for the removal of ``django.utils.six`` and
  ``python_2_unicode_compatible`` from the testsuite. They were only
  required for our dependencies, not for feincms3 itself.


`0.34`_ (2020-06-05)
~~~~~~~~~~~~~~~~~~~~

- Removed mentions of Python 2 compatibility in the docs.
- Allowed using ``render_list`` with lists, not only querysets.
- Dropped compatibility with Django<2.2 in accordance with the official
  Django releases support policy.
- Replaced ``url()`` with ``re_path()`` which avoids a few deprecation
  warnings.


`0.33`_ (2019-12-16)
~~~~~~~~~~~~~~~~~~~~

- Changed ``Regions``' ``cache_key`` argument handling to allow
  disabling caching by returning a falsy value.
- Added the ``feincms3.renderer.render_in_context`` utility.
- Verified compatibility with Django 3.0.
- Made the ``TemplateMixin.template`` property fall back to the first
  template in ``TEMPLATES`` if the specific template could not be found
  or does not exist.
- Fixed another path uniqueness validation problem where pages having
  descendants with static paths could not be saved.


`0.32`_ (2019-09-20)
~~~~~~~~~~~~~~~~~~~~

- Changed ``app_instance_namespace`` to ``blank=True`` to make it clear
  what the default value is.
- Fixed a possible path uniqueness problem with descendants with static
  paths.
- Dropped Python 3.4 compatibility.


`0.31`_ (2019-05-14)
~~~~~~~~~~~~~~~~~~~~

- Added copying of ``handler400``, ``handler403``, ``handler404`` and
  ``handler500`` from ``ROOT_URLCONF`` to the URLconf module created by
  ``apps_urlconf``.


Removed all deprecated features
-------------------------------

- The ``AppsMiddleware`` alias for ``apps_middleware`` has been removed.
- The ``feincms3.incubator`` module has has been removed including
  subrenderers.
- The ``depth`` and ``cte_path`` attributes of ``AbstractPage`` have
  been removed. Those helped with the transition from django-cte-forest
  to django-tree-queries almost one year ago.
- ``TemplatePluginRenderer.regions()`` and ``feincms3.renderer.Regions``
  are replaced by ``feincms3.regions.Regions``. Region timeouts must be
  specified when instantiating the ``feincms3.regions.Regions`` object
  and cannot be specified when rendering individual regions anymore.
- The ``feincms3_apps`` and ``feincms3_renderer`` template tag libraries
  have been replaced by a single ``feincms3`` tag library.


`0.30`_ (2019-03-18)
~~~~~~~~~~~~~~~~~~~~

- Fixed overflowing tree structure boxes in the ``TreeAdmin``.
- Switched to emitting ``DeprecationWarning`` warnings not ``Warning``,
  even though  their visibility sucks.
- Added a ``languages`` argument to ``reverse_app`` which allows
  overriding languages and their order.
- Made ``TreeAdmin`` and ``MoveForm`` only require that the default
  manager is a ``TreeQuerySet`` and not that the model itself also
  extends ``TreeNode``.
- Made ``plugin_ckeditor.js``\'s dependency on ``django.jQuery``
  explicit. This is necessary for Django 2.2's new ``Media.merge``
  algorithm.


`0.29`_ (2019-02-07)
~~~~~~~~~~~~~~~~~~~~

- Deprecated the ``feincms3_apps`` and ``feincms3_renderer`` template
  tag library. ``render_region`` and ``reverse_app`` have been made
  available as ``feincms3``. The ``render_plugin`` and
  ``render_plugins`` tags will be removed completely.
- Changed ``feincms3.regions.matches`` to the effect that ``None`` has
  to be provided explicitly as an allowed subregion if items with no
  ``subregion`` attribute should be matched too.
- Removed an use of six which is unnecessary now that we only support
  Python 3.
- Imported ``lru_cache`` from the Python library.
- Replaced ``concrete_model`` calls to determine the concrete subclass
  of ``AppsMixin`` with capturing the model instance locally in the
  ``class_prepared`` signal handler.
- Removed the now unused ``concrete_model`` and ``iterate_subclasses``
  utilities.
- Replaced two more occurrences of ``.objects`` with
  ``._default_manager``.
- Deprecated accessing the backwards compatibility properties
  ``AbstractPage.depth`` and ``AbstractPage.cte_path``.
- Deprecated ``feincms3.apps.AppsMiddleware`` in favor of
  ``feincms3.apps.apps_middleware``.


`0.28`_ (2019-02-03)
~~~~~~~~~~~~~~~~~~~~

- **(not yet) BACKWARDS INCOMPATIBLE** Deprecated
  ``TemplatePluginRenderer``'s ``regions`` method, the ``regions_class``
  attribute and ``feincms3.renderer.Regions``. Introduce the more
  versatile ``feincms3.regions.Regions`` class instead which also
  replaces the ``feincms3.incubator.subrenderer`` functionality and does
  not suffer from a software design problem where the regions and the
  renderer classes knew too much about each other. This has been
  bothering me for a long time already but became impossible to overlook
  in the subrenderer implementation.
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
.. _0.28: https://github.com/matthiask/feincms3/compare/0.27...0.28
.. _0.29: https://github.com/matthiask/feincms3/compare/0.28...0.29
.. _0.30: https://github.com/matthiask/feincms3/compare/0.29...0.30
.. _0.31: https://github.com/matthiask/feincms3/compare/0.30...0.31
.. _0.32: https://github.com/matthiask/feincms3/compare/0.31...0.32
.. _0.33: https://github.com/matthiask/feincms3/compare/0.32...0.33
.. _0.34: https://github.com/matthiask/feincms3/compare/0.33...0.34
.. _0.35: https://github.com/matthiask/feincms3/compare/0.34...0.35
.. _0.36: https://github.com/matthiask/feincms3/compare/0.35...0.36
.. _0.37: https://github.com/matthiask/feincms3/compare/0.36...0.37
.. _0.38.1: https://github.com/matthiask/feincms3/compare/0.37...0.38.1
.. _0.39: https://github.com/matthiask/feincms3/compare/0.38.1...0.39
.. _0.40: https://github.com/matthiask/feincms3/compare/0.39...0.40
.. _0.41: https://github.com/matthiask/feincms3/compare/0.40...0.41
.. _0.90b14: https://github.com/matthiask/feincms3/compare/0.41...0.90b14
.. _Next version: https://github.com/matthiask/feincms3/compare/0.90b14...main
