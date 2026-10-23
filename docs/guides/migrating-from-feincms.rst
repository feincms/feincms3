.. _migrating-from-feincms:

Migrating from FeinCMS
======================

FeinCMS is still maintained, but development mostly happens in feincms3 and
django-content-editor these days. This guide describes a gradual migration
which keeps the site in production the whole time and doesn't require
exporting and importing any content. It is based on migrations of large,
long-lived projects.

The guide covers projects using FeinCMS' bundled page module
(``feincms.module.page``) with content types. Other setups, for example custom
models built with ``create_base_model()`` or several independent content
trees, can be migrated using the same ideas but aren't covered here. If you
run into problems, please ask in the `feincms3 issue tracker
<https://github.com/feincms/feincms3/issues>`__.

The most important insight is that FeinCMS content types and feincms3 plugins
are so similar that both can use the same database tables. FeinCMS content
types have a ``parent`` foreign key, a ``region`` and an ``ordering`` field,
and so have plugins created by
:func:`content_editor.models.create_plugin_base`. As long as the remaining
fields stay the same, a feincms3 plugin model can be pointed at the table
FeinCMS created and both sides of the code base can read and write the same
rows.


Overview
~~~~~~~~

1. feincms3 plugin models are added alongside the content types with
   ``managed = False`` and ``db_table`` set to the existing table. FeinCMS
   keeps managing the tables for now.
2. The admin is moved from FeinCMS' ``ItemEditor`` to django-content-editor's
   ``ContentEditor``.
3. Rendering is moved from FeinCMS to feincms3, piece by piece: the frontend,
   search indexers, feeds, exports and everything else which renders content.
4. Once nothing uses FeinCMS anymore, FeinCMS' page model is replaced with
   your own, the migrations are recreated, and FeinCMS is removed from the
   project.
5. The page model is converted to :class:`~feincms3.pages.AbstractPage` and
   django-tree-queries.

The last two steps should be deployed together, see :ref:`the page model
<migrating-from-feincms-page-model>`.


Before you start
~~~~~~~~~~~~~~~~

Most surprises in a migration come from parts of FeinCMS which have no direct
feincms3 equivalent. It's worth making a list of those first:

- **Content types:** Their tables and columns. Content types which take
  arguments in ``create_content_type()`` (for example ``TYPE_CHOICES``) may add
  fields in ``initialize_type()``, so check the actual tables. Content types
  with ``process()`` or ``finalize()`` methods (forms, FeinCMS'
  ``ApplicationContent``) have to be replaced by :ref:`apps
  <apps-introduction>` or normal Django views.
- **Extensions:** Every extension adds fields to the page table. See the
  table in :ref:`the page model <migrating-from-feincms-page-model>` section
  for what happens to them.
- **Third party apps built on FeinCMS**, for example feincms-elephantblog,
  feincms-oembed, form_designer's FeinCMS content type or FeinCMS' media
  library. They have to be replaced or migrated separately.
- **Template tags and other FeinCMS APIs:** ``feincms_tags``,
  ``feincms_page_tags`` (``feincms_nav``, ``feincms_breadcrumbs``,
  ``feincms_translatedpage`` etc.), ``feincms.context_processors``,
  ``feincms.apps.app_reverse``, FeinCMS' sitemap. Navigation especially
  usually has to be rewritten, see :doc:`navigation`.
- **Code accessing content** through ``page.content``, see :ref:`rendering
  <migrating-from-feincms-rendering>`.
- **Rich text:** FeinCMS doesn't sanitize rich text by default. feincms3's
  :mod:`rich text plugin <feincms3.plugins.richtext>` sanitizes HTML using
  `html-sanitizer <https://pypi.org/project/html-sanitizer>`__ whenever a
  plugin is saved through a form. Existing content stays as it is until an
  editor saves it, at which point markup which isn't allowed by the sanitizer
  configuration is removed. Configure ``HTML_SANITIZERS`` or use a plugin of
  your own before switching the admin.


Plugins sharing tables with content types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``create_content_type`` generates the table name by appending the lowercased
class name (or the ``class_name`` argument) to the base model's table, so
``Page.create_content_type(RichTextContent)`` uses
``page_page_richtextcontent``. Look the table names up in your database or
your existing migrations instead of guessing.

The feincms3 plugins are added to an app of your own, for example ``cms``,
and look like this:

.. code-block:: python

    from content_editor.models import create_plugin_base
    from feincms.contrib.fields import JSONField
    from feincms.module.page.models import Page
    from feincms3 import plugins

    PagePlugin = create_plugin_base(Page)

    class RichText(plugins.richtext.RichText, PagePlugin):
        class Meta:
            db_table = "page_page_richtextcontent"
            managed = False  # Still owned by FeinCMS

    class Download(PagePlugin):
        title = models.CharField(max_length=100)
        data = JSONField(blank=True)

        class Meta:
            db_table = "page_page_downloadcontent"
            managed = False  # Still owned by FeinCMS

Things to watch out for:

- The plugin's fields have to match the existing columns exactly. If the
  bundled feincms3 plugin doesn't fit, write your own; plugins are just Django
  models. Sharing an abstract model between the FeinCMS content type and the
  feincms3 plugin is a good way to keep both in sync during the migration.
- FeinCMS' ``RichTextField`` is a ``TextField`` and can be replaced by
  ``models.TextField`` or feincms3's
  :class:`~feincms3.cleanse.CleansedRichTextField` without changing the
  database.
- FeinCMS' ``JSONField`` uses a text column too, but converts values to and
  from dictionaries in Python. Keep using it in the plugins as long as FeinCMS
  is installed; a ``models.TextField`` would hand your code strings such as
  ``""`` or ``'{"a": 1}'``. See :ref:`migrating-from-feincms-jsonfield` for
  switching to Django's ``models.JSONField`` when removing FeinCMS.
- The plugin class name doesn't have to match the content type's class name.
  The reverse accessors are different though (for example
  ``richtextcontent_set`` vs. ``cms_richtext_set``), and the plugin is a
  separate model with its own row in ``django_content_type`` and its own
  permissions. See :ref:`permissions <migrating-from-feincms-permissions>` below.


.. _migrating-from-feincms-admin:

Admin
~~~~~

Replace FeinCMS' page admin with one based on
:class:`content_editor.admin.ContentEditor` and add inlines for the plugins,
see :ref:`build-your-cms`. Set ``FEINCMS_USE_PAGE_ADMIN = False`` so that
FeinCMS doesn't register its own admin for the page model.

The content editor and the feincms3 renderer expect the regions in a
``regions`` attribute. Your own page model will get it from
:class:`~feincms3.mixins.TemplateMixin` or
:class:`~feincms3.applications.PageTypeMixin` later, but FeinCMS' page model
doesn't have it. FeinCMS' regions already have the ``key``, ``title`` and
``inherited`` attributes django-content-editor needs, so a temporary property
pointing at the regions of the page's FeinCMS template is enough while the
migration is in progress.

FeinCMS' ``TreeEditor`` doesn't work together with ``ContentEditor``, but
django-mptt's ``DraggableMPTTAdmin`` does. FeinCMS' ``PageAdminForm`` can be
reused as well; it validates URLs and prevents moving pages below themselves:

.. code-block:: python

    from content_editor.admin import ContentEditor, ContentEditorInline
    from django.contrib import admin
    from feincms.module.page.forms import PageAdminForm
    from feincms.module.page.models import Page
    from feincms3 import plugins
    from mptt.admin import DraggableMPTTAdmin

    from app.cms import models

    # Temporary, until the page model is replaced
    Page.regions = property(lambda self: self.template.regions)

    @admin.register(Page)
    class PageAdmin(DraggableMPTTAdmin, ContentEditor):
        form = PageAdminForm
        list_display = ["tree_actions", "indented_title", "active"]
        list_display_links = ["indented_title"]
        prepopulated_fields = {"slug": ["title"]}
        inlines = [
            plugins.richtext.RichTextInline.create(models.RichText),
            ContentEditorInline.create(models.Download),
            ...
        ]

FeinCMS' page admin also adds the fields of extensions to its fieldsets.
Your admin has to list them itself if you define ``fieldsets``.

.. _migrating-from-feincms-permissions:

Django's admin checks the permissions of inline models too. Users who aren't
superusers need the ``add``, ``change``, ``delete`` and ``view`` permissions
of each plugin model, otherwise the plugins are read-only or missing in the
content editor. Groups and users only have the permissions of the FeinCMS
content types (for example ``page.add_richtextcontent``) and not those of the
new plugin models (for example ``cms.add_richtext``), even though both use
the same table. Django creates the permissions for the plugin models when
running ``migrate``, also for models with ``managed = False``.

Often this isn't worth more than a few clicks: if all editors are superusers,
or if there are only a few groups, simply assign the new permissions in the
admin. Copying the assignments programmatically is only worth it if
permissions are used heavily, for example with many groups or with
permissions assigned to individual users. In that case run something like
this when switching the admin, for example in ``./manage.py shell``:

.. code-block:: python

    from django.contrib.auth.models import Permission

    # Old model -> new model
    MODELS = {
        "page.richtextcontent": "cms.richtext",
        "page.downloadcontent": "cms.download",
        # When replacing the page model, see below:
        # "page.page": "cms.page",
    }

    for old, new in MODELS.items():
        old_app_label, old_model = old.split(".")
        new_app_label, new_model = new.split(".")
        for action in ("add", "change", "delete", "view"):
            old_perm = Permission.objects.get(
                content_type__app_label=old_app_label,
                codename=f"{action}_{old_model}",
            )
            new_perm = Permission.objects.get(
                content_type__app_label=new_app_label,
                codename=f"{action}_{new_model}",
            )
            for group in old_perm.group_set.all():
                group.permissions.add(new_perm)
            for user in old_perm.user_set.all():
                user.user_permissions.add(new_perm)

Anything else referencing content types has the same problem, for example
generic foreign keys or the admin's change history.


.. _migrating-from-feincms-rendering:

Rendering
~~~~~~~~~

FeinCMS content types render themselves through their ``render()`` method.
feincms3 keeps rendering separate from the models: a
:class:`~feincms3.renderer.RegionRenderer` decides how each plugin is
rendered. The same plugins can therefore be rendered differently in different
places, for example on the website, in a search index or in a newsletter, and
the renderer also supports subregions, caching and region inheritance. See
:doc:`rendering` for the details.

For a site using FeinCMS' basic region rendering the switch is small though.
Register the plugins with a renderer and add the regions to the template
context. FeinCMS' page view can be kept for now; it still handles FeinCMS'
request processors, redirects and ``ApplicationContent``:

.. code-block:: python

    from feincms.views import Handler
    from feincms3.renderer import RegionRenderer, template_renderer

    from app.cms import models

    renderer = RegionRenderer()
    renderer.register(
        models.RichText,
        template_renderer("plugins/richtext.html"),
    )
    ...

    class PageHandler(Handler):
        def get_context_data(self, **kwargs):
            page = self.object
            return super().get_context_data(
                regions=renderer.regions_from_item(
                    page,
                    # Required for regions marked as "inherited"
                    inherit_from=page.get_ancestors(ascending=True),
                    timeout=60,
                ),
                **kwargs,
            )

Use the view instead of ``feincms.views.Handler`` in your URLconf, keeping
the ``feincms_home`` and ``feincms_handler`` URL names which FeinCMS' page
model uses to build URLs. Templates then use ``{% render_region %}`` instead
of ``{% feincms_render_region %}``:

.. code-block:: html

    {% load feincms3 %}

    {# Before: {% feincms_render_region feincms_page "main" request %} #}
    {% render_region regions "main" %}

FeinCMS' content type templates usually access the model instance as
``content``, while :func:`~feincms3.renderer.template_renderer` passes it as
``plugin`` by default. Existing templates can be reused without changes by
providing the context yourself:

.. code-block:: python

    renderer.register(
        models.RichText,
        template_renderer(
            "content/richtext/default.html",
            lambda plugin, context: {"content": plugin},
        ),
    )

Existing ``render()`` methods don't have to be rewritten right away if the
plugins inherit them, for example from a shared abstract model. A small
renderer function can call them; FeinCMS' ``render()`` methods return either
HTML or a ``(template, context)`` tuple:

.. code-block:: python

    from feincms3.renderer import render_in_context

    def render_feincms_content(plugin, context):
        html = plugin.render(request=context.get("request"), context=context)
        if isinstance(html, (list, tuple)):
            return render_in_context(context, *html)
        return html

    renderer.register(models.Download, render_feincms_content)

Search indexers, feeds, management commands and other code accessing
``page.content.main`` or ``page.content.all_of_type(...)`` have to be
converted too. A content proxy which complains makes those places easy to
find. Start with warnings, switch to exceptions once you're confident that
everything has been converted:

.. code-block:: python

    import warnings

    from feincms.models import ContentProxy

    class WarningContentProxy(ContentProxy):
        def __init__(self, item):
            warnings.warn(
                f"Content of {item!r} accessed through the FeinCMS content proxy",
                RuntimeWarning,
                stacklevel=3,
            )
            super().__init__(item)

    Page.content_proxy_class = WarningContentProxy

FeinCMS' ``ApplicationContent`` can be replaced by feincms3's
:class:`~feincms3.applications.ApplicationType` and
:class:`~feincms3.applications.PageTypeMixin`. Note that the app URLconfs are
assembled differently, see :ref:`apps-introduction`.

If you're using FeinCMS' ``ct_tracker`` extension, its inventory is reset
when the page is saved, which the content editor does. Code which adds or
removes plugins without saving the page has to reset ``_ct_inventory`` itself
as long as FeinCMS renders some of the content.


Handing the tables over to the feincms3 plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step is only necessary if you want to remove FeinCMS content types one by
one while the rest of the migration is still in progress. If you're going to
recreate the migrations from scratch at the end anyway (see :ref:`the page
model <migrating-from-feincms-page-model>`), remove ``managed = False`` at that
point and skip this section.

Once nothing uses a FeinCMS content type anymore, remove the
``create_content_type`` call and ``managed = False`` in the same commit, so
that there's never more than one managed model using the table. For the
plugin, ``makemigrations`` only generates an ``AlterModelOptions`` operation,
which doesn't touch the database. For the content type it generates a
``DeleteModel`` operation which would drop the table, including all plugins.

Move the ``DeleteModel`` operation into the ``state_operations`` of a
:class:`~django.db.migrations.operations.SeparateDatabaseAndState` operation,
leaving ``database_operations`` empty:

.. code-block:: python

    class Migration(migrations.Migration):
        dependencies = [
            ("page", "0011_previous_migration"),
        ]

        operations = [
            migrations.SeparateDatabaseAndState(
                state_operations=[
                    migrations.DeleteModel(name="RichTextContent"),
                ],
                # No database_operations, the table now belongs to the plugin.
            ),
        ]

``db_table`` can stay in the plugin's ``Meta`` forever; it isn't harmful.
Plugins added later don't need it.

As always, try this on a copy of the production database first and make sure
you have backups.


.. _migrating-from-feincms-page-model:

The page model
~~~~~~~~~~~~~~

The last step is replacing FeinCMS' page model with one of your own. The page
model belongs to the ``page`` app inside FeinCMS, usually with migrations
living in your project through ``MIGRATION_MODULES``. Those migrations
reference FeinCMS, and the ``page`` app label disappears together with
FeinCMS, so their history can't be kept.

Add a ``Page`` model to your ``cms`` app which matches the existing
``page_page`` table exactly, including the fields added by FeinCMS extensions,
and set ``db_table = "page_page"``. Copy the field definitions from FeinCMS'
``BasePage``, the extensions and your ``page`` migrations;
``./manage.py inspectdb page_page`` helps with checking the columns, but loses
indexes, check constraints and ``on_delete`` behavior. Keep django-mptt's
``MPTTModel`` as the base class for now so that the page tree keeps working
until it is converted to django-tree-queries.

Point the plugins' foreign keys and all other foreign keys to ``page.Page`` at
the new model, switch the plugins' ``JSONField`` to ``models.TextField``
(see :ref:`migrating-from-feincms-jsonfield`) and remove FeinCMS from
``INSTALLED_APPS``, ``MIGRATION_MODULES`` and your requirements.

Add :class:`~feincms3.mixins.TemplateMixin` (or
:class:`~feincms3.applications.PageTypeMixin`) to the new model; its
``template_key`` field uses the column FeinCMS created. FeinCMS' column allows
255 characters while ``TemplateMixin`` only allows 100, so either override the
field for now or shorten it in a later migration. The template keys have to
stay the same. A small helper can convert the definitions passed to
FeinCMS' ``register_templates()`` so that they don't have to be rewritten:

.. code-block:: python

    from content_editor.models import Region, Template
    from feincms3.mixins import TemplateMixin
    from mptt.models import MPTTModel

    # The definitions previously passed to Page.register_templates()
    FEINCMS_TEMPLATES = [
        {
            "key": "base",
            "title": _("default"),
            "path": "cms/standard.html",
            "regions": (
                ("main", _("Main content area")),
                ("sidebar", _("Sidebar"), "inherited"),
            ),
        },
    ]

    def to_templates(templates):
        return [
            Template(
                key=t["key"],
                title=t["title"],
                template_name=t["path"],
                regions=[
                    Region(key=key, title=title, inherited=rest[:1] == ["inherited"])
                    for key, title, *rest in t["regions"]
                ],
            )
            for t in templates
        ]

    class Page(MPTTModel, TemplateMixin):
        TEMPLATES = to_templates(FEINCMS_TEMPLATES)

        # The fields of FeinCMS' page model and its extensions
        ...

        class Meta:
            db_table = "page_page"
            ordering = ["tree_id", "lft"]

When using :class:`~feincms3.applications.PageTypeMixin`, build
:class:`~feincms3.applications.TemplateType` instances instead and add them to
``TYPES``. Drop the temporary ``Page.regions`` property from the :ref:`admin
<migrating-from-feincms-admin>` step and use the new model in the admin.

Then recreate the migrations from scratch. Delete the ``page`` migrations, the
migrations of the ``cms`` app and the migrations of all other apps which
reference FeinCMS or depend on ``page`` migrations, and run ``./manage.py
makemigrations``. Existing databases already have all those tables, so the
history has to be reset and the new migrations marked as applied without
running them:

.. code-block:: sql

    DELETE FROM django_migrations WHERE app IN ('page', 'cms', ...);

.. code-block:: shell

    ./manage.py migrate --fake-initial

Delete the rows before running ``migrate`` the first time with the new
migrations, for example by adding the statement to the deployment. If the old
rows are still there, Django considers new migrations applied if they happen
to have the same name as an old one, for example ``cms.0001_initial``, and
skips them without any warning.

``--fake-initial`` only checks that the tables and columns exist, not that
they match. Compare the output of ``pg_dump --schema-only`` of the existing
database and of a database created from scratch before deploying this. The
column order may differ, which is harmless; index and constraint names are
derived from the table and column names and should be identical. Keep a copy
of any hand-written migrations (for example ones adding database triggers or
functions, or data migrations which new databases need too) and add them back
to the new migrations.

Instead of recreating the migrations of apps other than ``page`` you can also
edit FeinCMS out of them: Replace ``feincms.contrib.richtext`` and
``feincms.contrib.fields`` fields with ``models.TextField``, drop
``feincms.extensions.base.ExtensionsMixin``,
``feincms.module.mixins.ContentModelMixin`` and
``feincms.translations.TranslatedObjectMixin`` from ``bases`` (they only add
behavior, no fields) and replace references to ``page.Page`` and to ``page``
migrations with the new model and its initial migration. This is more work
but keeps the history intact, which is useful if those apps contain many
hand-written migrations.

``cms.Page`` has its own row in ``django_content_type`` and its own
permissions. Copy the permission assignments as described in :ref:`permissions
<migrating-from-feincms-permissions>` before removing stale content types.

The new model doesn't contain FeinCMS' ``save()`` logic which keeps
``_cached_url`` up to date and propagates ``active`` to descendants. Convert
it to :class:`~feincms3.pages.AbstractPage` using normal migrations in the
same deployment, so that the site never runs with the intermediate model:

================================================ =====================================================
FeinCMS                                          feincms3
================================================ =====================================================
``active``                                       ``is_active`` (:class:`~feincms3.pages.AbstractPage`)
``title``, ``parent``                            same names
``slug``                                         ``slug``; FeinCMS allows 150 characters, feincms3 50
                                                 by default. Override the field to keep the length.
``_cached_url``, ``override_url``                ``path``, ``static_path``; ``path`` has to be
                                                 unique, FeinCMS only prevents duplicate URLs among
                                                 active pages.
``lft``, ``rght``, ``tree_id``, ``level``        ``position``, see below
``template_key``                                 ``template_key`` (:class:`~feincms3.mixins.TemplateMixin`)
``in_navigation``, ``navigation_group``          ``menu`` (:class:`~feincms3.mixins.MenuMixin`)
``redirect_to``                                  ``redirect_to_page`` if the value looks like
                                                 ``page.page:42``, ``redirect_to_url`` otherwise
                                                 (:class:`~feincms3.mixins.RedirectMixin`)
``language``, ``translation_of``                 ``language_code``, ``translation_of``
                                                 (:class:`~feincms3.mixins.LanguageAndTranslationOfMixin`)
``meta_keywords``, ``meta_description``          `feincms3-meta <https://github.com/matthiask/feincms3-meta>`__
``publication_date``, ``publication_end_date``   no equivalent; keep the fields and filter
                                                 in your queryset if you need them
``_ct_inventory``, ``navigation_extension``      no equivalent; drop
================================================ =====================================================

Check for duplicate URLs before adding the unique constraint:

.. code-block:: sql

    SELECT _cached_url, COUNT(*) FROM page_page GROUP BY 1 HAVING COUNT(*) > 1;

FeinCMS uses django-mptt for the page tree, feincms3 uses django-tree-queries.
The django-tree-queries documentation has a `guide for migrating from
django-mptt <https://django-tree-queries.readthedocs.io/en/latest/#migrating-from-django-mptt>`__.

The page view, URLconf, navigation and anything else which still depends on
FeinCMS' page model have to be replaced in the same deployment too, see
:ref:`build-your-cms`.

Once that's done, ``db_table`` can be removed too if you want; Django then
renames the table to ``cms_page``.


.. _migrating-from-feincms-jsonfield:

Converting FeinCMS' ``JSONField``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FeinCMS' ``JSONField`` stores JSON in a text column and is forgiving when
reading it: empty strings, ``NULL`` and invalid JSON are all returned as an
empty ``dict``. When saving, empty values are stored as empty strings.

Django's ``models.JSONField`` is stricter. It uses a ``jsonb`` column on
PostgreSQL and a ``JSON_VALID`` check constraint on SQLite, and the
``AlterField`` operation which ``makemigrations`` generates for the switch
fails as soon as it encounters a value which isn't valid JSON. On PostgreSQL
the column is converted using a ``USING data::jsonb`` cast, and
``''::jsonb`` is an error.

When recreating the migrations, use ``models.TextField`` for the field so that
the initial migration matches the existing column. Then switch the field to
``models.JSONField``, run ``makemigrations`` again and add a data migration
which fixes the raw strings before the ``AlterField`` runs. Code using the
field sees strings while it is a ``TextField``, so deploy both migrations
together:

.. code-block:: python

    import json

    from django.db import migrations, models


    def clean_json(apps, schema_editor):
        Model = apps.get_model("cms", "Download")
        for pk, value in Model.objects.values_list("pk", "data"):
            try:
                json.loads(value)
            except (TypeError, ValueError):
                # Empty strings, NULL and invalid JSON were all an empty
                # dict for FeinCMS.
                Model.objects.filter(pk=pk).update(data="{}")


    class Migration(migrations.Migration):
        dependencies = [
            ("cms", "0001_initial"),
        ]

        operations = [
            migrations.RunPython(clean_json, migrations.RunPython.noop),
            migrations.AlterField(
                model_name="download",
                name="data",
                field=models.JSONField(blank=True, default=dict),
            ),
        ]

On PostgreSQL 16 and newer you can find the offending rows up front with
``SELECT id, data FROM page_page_downloadcontent WHERE data IS NULL OR data IS NOT JSON``.
It's a good idea to look at them before deciding to throw them away; invalid
JSON is lost silently in the migration above, just like FeinCMS silently
ignored it.

Code using the field may need small adjustments too. FeinCMS always returned a
``dict``, Django returns whatever was stored, including lists, strings or
``None`` for nullable fields. ``default=dict`` keeps the behavior for new
rows.
