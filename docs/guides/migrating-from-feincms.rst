.. _migrating-from-feincms:

Migrating from FeinCMS
======================

FeinCMS is still maintained, but development mostly happens in feincms3 and
django-content-editor these days. This guide describes a gradual migration
which keeps the site in production the whole time and doesn't require
exporting and importing any content. It is based on migrations of large,
long-lived projects.

The guide covers projects using FeinCMS' bundled page module
(``feincms.module.page``) with content types. Other FeinCMS base models, for
example feincms-elephantblog's entries or models of your own built with
``create_base_model()``, can be migrated the same way; see :ref:`other base
models <migrating-from-feincms-other-base-models>`. If you run into problems,
please ask in the `feincms3 issue tracker
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

Steps 1 to 3 can be deployed one by one. The last two steps should be deployed
together, see :ref:`the page model <migrating-from-feincms-page-model>`.
Whatever you do, :ref:`compare the site before and after
<migrating-from-feincms-verifying>` each step.


Before you start
~~~~~~~~~~~~~~~~

Most surprises in a migration come from parts of FeinCMS which have no direct
feincms3 equivalent. It's worth making a list of those first:

- **Base models:** FeinCMS' page model may not be the only model using content
  types. feincms-elephantblog's ``Entry`` and models built with
  ``create_base_model()`` have to be migrated too before FeinCMS can be
  removed.
- **Content types:** Their tables and columns. Content types which take
  arguments in ``create_content_type()`` (for example ``TYPE_CHOICES``) may add
  fields in ``initialize_type()``, so check the actual tables. Content types
  with ``process()`` or ``finalize()`` methods (forms, FeinCMS'
  ``ApplicationContent``) have to be replaced by :ref:`apps
  <apps-introduction>` or normal Django views. Content types without any rows
  can often simply be dropped.
- **Extensions:** Every extension adds fields to the page table. See the
  table in :ref:`the page model <migrating-from-feincms-page-model>` section
  for what happens to them.
- **Third party apps:** feincms-elephantblog and form_designer's FeinCMS
  content type depend on FeinCMS and have to be replaced. feincms-oembed and
  feincms-cleanse don't depend on FeinCMS and can stay.
- **Template tags and other FeinCMS APIs:** ``feincms_tags``,
  ``feincms_page_tags`` (``feincms_nav``, ``feincms_languagelinks``,
  ``page_is_active`` etc.), ``feincms_thumbnail``,
  ``feincms.context_processors``, ``feincms.apps.app_reverse`` and
  ``permalink``, ``feincms.translations``, FeinCMS' sitemap. Navigation
  especially usually has to be rewritten, see :doc:`navigation`.
- **Code accessing content** through ``page.content`` or through the content
  types' reverse accessors, for example ``{{
  entry.filerimagecontent_set.first.mediafile.url }}`` in templates. The
  plugins' reverse accessors have different names.
- **Translations:** Templates may use strings which are only translated in
  the locale files of FeinCMS or elephantblog. Those translations disappear
  together with the apps.
- **Rich text:** FeinCMS doesn't sanitize rich text by default. Define a
  rich text plugin using django-prose-editor as described in
  :ref:`richtext-prose-editor`; feincms3's bundled rich text plugin is
  deprecated since it uses CKEditor 4. With ``sanitize=True``, HTML is sanitized whenever a plugin is
  saved through a form. Existing content stays as it is until an editor saves
  it, at which point markup which the configured extensions don't support is
  removed. Configure the extensions accordingly before switching the admin.


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
    from django_prose_editor.fields import ProseEditorField
    from feincms.contrib.fields import JSONField
    from feincms.module.page.models import Page

    PagePlugin = create_plugin_base(Page)

    class RichText(PagePlugin):
        text = ProseEditorField(extensions={...}, sanitize=True)

        class Meta:
            db_table = "page_page_richtextcontent"
            managed = False  # Still owned by FeinCMS
            ordering = ["ordering"]

    class Download(PagePlugin):
        title = models.CharField(max_length=100)
        data = JSONField(blank=True)

        class Meta:
            db_table = "page_page_downloadcontent"
            managed = False  # Still owned by FeinCMS
            ordering = ["ordering"]

Things to watch out for:

- The plugin's fields have to match the existing columns exactly. If the
  bundled feincms3 plugin doesn't fit, write your own; plugins are just Django
  models. A set of abstract models shared between the plugins of all base
  models (pages, blog entries, ...) keeps the code short.
- A ``Meta`` class in the plugin replaces the ``Meta`` of
  ``create_plugin_base``, including ``ordering = ["ordering"]``. Without it,
  ``page.cms_richtext_set.first()`` returns the plugin with the lowest primary
  key instead of the first one. Repeat ``ordering`` or inherit from the base's
  ``Meta`` explicitly.
- FeinCMS' ``RichTextField`` is a ``TextField`` and can be replaced by
  ``models.TextField`` or django-prose-editor's ``ProseEditorField`` without
  changing the database.
- FeinCMS' ``JSONField`` uses a text column too, but converts values to and
  from dictionaries in Python. Keep using it in the plugins as long as FeinCMS
  is installed; a ``models.TextField`` would hand your code strings such as
  ``""`` or ``'{"a": 1}'``. See :ref:`migrating-from-feincms-jsonfield` for
  switching to Django's ``models.JSONField`` when removing FeinCMS.
- Many-to-many fields need an explicit through model with ``managed = False``
  and ``db_table`` set to the existing table. Django creates the automatic
  through model as a managed model if either side is managed, so ``migrate``
  would try to create the table and the system checks complain that two
  models use it. Once FeinCMS is gone the automatic through model works
  again, but its column names are derived from the class name of the plugin
  (``articlesteaserlistcontent_id``), so keeping the content type's class name
  for such plugins saves a migration.
- The plugin class name doesn't have to match the content type's class name.
  The reverse accessors are different though (for example
  ``richtextcontent_set`` vs. ``cms_richtext_set``), and the plugin is a
  separate model with its own row in ``django_content_type`` and its own
  permissions. See :ref:`permissions <migrating-from-feincms-permissions>` below.
- Plugins referencing other models with a ``related_name`` which FeinCMS'
  content type uses as well need a different ``related_name`` (for example
  ``"+"``) until the content type is gone.


.. _migrating-from-feincms-admin:

Admin
~~~~~

Replace FeinCMS' page admin with one based on
:class:`content_editor.admin.ContentEditor` and add inlines for the plugins,
see :ref:`build-your-cms`. Set ``FEINCMS_USE_PAGE_ADMIN = False`` so that
FeinCMS doesn't register its own admin for the page model. Admins of third
party apps have to be unregistered first.

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
            ContentEditorInline.create(models.RichText, icon="notes"),
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

Check who actually depends on those permissions; editors are often in a
group or two, sometimes superusers. If only a few groups are affected, simply
assign the new permissions in the admin. Otherwise copy the assignments in a
data migration, so that they are copied automatically when deploying. Django
creates the permissions of new models only after all migrations have run,
so the migration has to create them first:

.. code-block:: python

    from django.contrib.auth.management import create_permissions
    from django.db import migrations

    # Old model -> new model using the same table
    MODELS = {
        "page.richtextcontent": "cms.richtext",
        "page.downloadcontent": "cms.download",
        # When replacing the page model, see below:
        # "page.page": "cms.page",
    }

    def copy_permissions(apps, schema_editor):
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, apps=apps, verbosity=0)
            app_config.models_module = None

        Permission = apps.get_model("auth", "Permission")
        for old, new in MODELS.items():
            old_app_label, old_model = old.split(".")
            new_app_label, new_model = new.split(".")
            for old_perm in Permission.objects.filter(
                content_type__app_label=old_app_label,
                content_type__model=old_model,
            ):
                action = old_perm.codename.split("_", 1)[0]
                new_perm = Permission.objects.filter(
                    content_type__app_label=new_app_label,
                    content_type__model=new_model,
                    codename=f"{action}_{new_model}",
                ).first()
                if new_perm:
                    new_perm.group_set.add(*old_perm.group_set.all())
                    new_perm.user_set.add(*old_perm.user_set.all())

    class Migration(migrations.Migration):
        dependencies = [
            ("auth", "0012_alter_user_first_name_max_length"),
            ("contenttypes", "0002_remove_content_type_name"),
            ("cms", "0004_previous_migration"),
        ]

        operations = [
            migrations.RunPython(copy_permissions, migrations.RunPython.noop),
        ]

The old permissions and content types stay in the database, so the migration
also works after FeinCMS has been removed, as long as the stale content types
haven't been deleted yet. On new databases it does nothing.

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
                    # Leave this out if the regions contain the output of
                    # applications, it depends on the URL
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

Templates of views you don't control, for example those of third party apps,
don't have a ``regions`` variable. A small template tag helps there:

.. code-block:: python

    @register.simple_tag(takes_context=True)
    def render_item_region(context, item, region):
        return renderer.regions_from_item(item).render(region, context)

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

Some content types rendered their templates with ``render_to_string`` and
therefore without the surrounding template context, while
``template_renderer`` renders them inside the current context. This rarely
matters, but variables of the surrounding template become visible in the
plugin templates.

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

If you're using FeinCMS' ``ct_tracker`` extension, its inventory is reset
when the page is saved, which the content editor does. Code which adds or
removes plugins without saving the page has to reset ``_ct_inventory`` itself
as long as FeinCMS renders some of the content.


.. _migrating-from-feincms-applicationcontent:

``ApplicationContent``
----------------------

FeinCMS inserts the output of an ``ApplicationContent`` at its position in the
region, between the other content types; a page may for example show a rich
text, the list of team members and a contact form below the list. While the
rendering is being converted, a plugin using the ``ApplicationContent``
table can output what FeinCMS' page view produced. Don't cache regions
containing application output; the output depends on the URL.

.. code-block:: python

    from feincms.content.application.models import ApplicationContent

    class Application(PagePlugin):
        class Meta:
            db_table = "page_page_applicationcontent"
            managed = False  # Still owned by FeinCMS
            ordering = ["ordering"]

    def render_application(plugin, context):
        # FeinCMS' page view processed the ApplicationContent instances of the
        # page already, the output is stored on them.
        page = context["feincms_page"]
        for content in page.content.all_of_type(
            page.content_type_for(ApplicationContent)
        ):
            if content.pk == plugin.pk:
                return content.render()
        return ""

feincms3 apps work differently: a page either uses a template or is an app,
and the app's views render complete responses. When replacing the page model,
:class:`~feincms3.applications.ApplicationType` page types replace the
``ApplicationContent`` instances. The plugin can stay as a marker for the
position of the app's output; views which rendered fragments render them
into the page's template:

.. code-block:: python

    def render_application(plugin, context):
        return context.get("app_content", "")

    class AppContentMixin:
        def render_to_response(self, context, **response_kwargs):
            page = page_for_app_request(self.request)
            return render(
                self.request,
                page.type.template_name,
                {
                    "page": page,
                    "regions": renderer.regions_from_item(page),
                    "app_content": render_to_string(
                        self.get_template_names(), context, request=self.request
                    ),
                },
            )

    class TeamView(AppContentMixin, ListView):
        ...

Views which used FeinCMS' "inheritance 2.0" and returned a ``(template,
context)`` tuple just become normal views; a context processor can provide the
page for their templates and for error pages, replacing
``feincms.context_processors.add_page_if_missing``. Remember to add
``app_name`` to the apps' URLconfs and to replace ``app_reverse(viewname,
urlconf)`` with :func:`~feincms3.applications.reverse_app` (note the swapped
arguments).

FeinCMS prefers pages over applications: a page below an application page,
for example ``/en/topics/energy/`` below the topics app at ``/en/topics/``, is
shown as a page. feincms3 sends all URLs below the app's page to the app. If
your site has such pages, check for them before calling the app's view:

.. code-block:: python

    def page_first(view):
        @wraps(view)
        def inner(request, *args, **kwargs):
            if Page.objects.active().filter(
                path=request.path_info, app_namespace=""
            ).exists():
                return page_detail(request, request.path_info.strip("/"))
            return view(request, *args, **kwargs)

        return inner

    # In the app's URLconf
    urlpatterns = [
        path("<slug:slug>/", page_first(views.topic_detail), name="topic_detail"),
    ]


Handing the tables over to the feincms3 plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step is only necessary if you want to remove FeinCMS content types one by
one while the rest of the migration is still in progress. If you're going to
recreate the migrations from scratch at the end anyway (see :ref:`the page
model <migrating-from-feincms-page-model>`), remove ``managed = False`` at that
point and skip this section.

Once nothing uses a FeinCMS content type anymore, remove the
``create_content_type`` call and ``managed = False`` in the same commit, so
that there's never more than one managed model using the table. None of the
operations ``makemigrations`` generates may touch the database:

- For the content type it generates ``RemoveField`` operations for its foreign
  keys and a ``DeleteModel`` operation. Together they would drop the table,
  including all plugins.
- Django doesn't add the relational fields of unmanaged models to the
  migration state. Once the plugins are managed, ``makemigrations`` adds them
  with ``AddField`` operations, but only when running it a second time. Those
  operations would try to add columns which exist already. ``makemigrations``
  asks for defaults for the foreign keys; ``./manage.py makemigrations
  --dry-run -v 3`` prints the operations without asking.

Move all of those operations into the ``state_operations`` of a
:class:`~django.db.migrations.operations.SeparateDatabaseAndState` operation
and leave ``database_operations`` empty. ``./manage.py sqlmigrate`` should
print nothing but ``BEGIN;`` and ``COMMIT;``:

.. code-block:: python

    class Migration(migrations.Migration):
        dependencies = [
            ("page", "0011_previous_migration"),
            ("cms", "0004_previous_migration"),
        ]

        operations = [
            migrations.SeparateDatabaseAndState(
                state_operations=[
                    migrations.RemoveField(
                        model_name="richtextcontent", name="parent"
                    ),
                    migrations.DeleteModel(name="RichTextContent"),
                    migrations.AddField(
                        model_name="richtext",
                        name="parent",
                        field=models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="%(app_label)s_%(class)s_set",
                            to="page.page",
                        ),
                    ),
                ],
                # No database_operations, the table now belongs to the plugin.
            ),
            migrations.AlterModelOptions(...),
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
indexes, check constraints and ``on_delete`` behavior. This intermediate model
only exists to generate the initial migration; the page model is converted to
feincms3 right afterwards (see below).

Point the plugins' foreign keys and all other foreign keys to ``page.Page`` at
the new model, switch the plugins' ``JSONField`` to ``models.TextField``
(see :ref:`migrating-from-feincms-jsonfield`), remove ``managed = False`` from
the plugins and remove FeinCMS from ``INSTALLED_APPS``, ``MIGRATION_MODULES``
and your requirements.

Then recreate the migrations from scratch. Delete the ``page`` migrations, the
migrations of the ``cms`` app and the migrations of all other apps which
reference FeinCMS or depend on ``page`` migrations, and run ``./manage.py
makemigrations``. Apps with foreign keys pointing at each other get a
``0001_initial`` and a ``0002_initial`` migration; both are initial
migrations. Existing databases already have all those tables, so the history
has to be reset and the new migrations marked as applied without running
them:

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
they match. Compare the schema of the existing database with the schema of a
database created from scratch, see :ref:`verifying the migration
<migrating-from-feincms-verifying>`. Long-lived databases rarely match their
migrations exactly: indexes created by old Django versions have different
names, and some constraints may never have been created at all (for example
the ``unique_together`` of ``feincms.translations.Translation``). Make the new
models match the existing database, and add missing constraints later with
normal migrations. Keep a copy of any hand-written migrations (for example
ones adding database triggers or functions, or data migrations which new
databases need too) and add them back to the new migrations.

Instead of recreating the migrations of apps other than ``page`` you can also
edit FeinCMS out of them: Replace ``feincms.contrib.richtext`` and
``feincms.contrib.fields`` fields with ``models.TextField``, drop
``feincms.extensions.base.ExtensionsMixin``,
``feincms.module.mixins.ContentModelMixin`` and
``feincms.translations.TranslatedObjectMixin`` from ``bases`` (they only add
behavior, no fields) and replace references to ``page.Page`` and to ``page``
migrations with the new model and its initial migration. This is more work
and gets complicated quickly when apps reference each other in both
directions, but keeps the history intact, which is useful if those apps
contain many hand-written migrations.

``cms.Page`` has its own row in ``django_content_type`` and its own
permissions, as do the models replacing those of third party apps. Copy the
permission assignments as described in :ref:`permissions
<migrating-from-feincms-permissions>`, for example in a migration running
after the recreated initial migrations, and before removing stale content
types.


Converting the page model
-------------------------

The intermediate model doesn't contain FeinCMS' ``save()`` logic which keeps
``_cached_url`` up to date and propagates ``active`` to descendants, and the
page tree isn't maintained anymore. Convert it to
:class:`~feincms3.pages.AbstractPage` using normal migrations in the same
deployment, so that the site never runs with the intermediate model:

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
``lft``, ``rght``, ``tree_id``, ``level``        ``position``
``template_key``                                 ``page_type`` (:class:`~feincms3.applications.PageTypeMixin`)
                                                 or ``template_key`` (:class:`~feincms3.mixins.TemplateMixin`)
``ApplicationContent``                           ``page_type`` and ``app_namespace``
``in_navigation``, ``navigation_group``          ``menu`` (:class:`~feincms3.mixins.MenuMixin`)
``redirect_to``                                  ``redirect_to_page`` if the value looks like
                                                 ``page.page:42``, ``redirect_to_url`` otherwise
                                                 (:class:`~feincms3.mixins.RedirectMixin`)
``language``, ``translation_of``                 ``language_code``, ``translation_of``
                                                 (:class:`~feincms3.mixins.LanguageAndTranslationOfMixin`)
``meta_keywords``, ``meta_description``          keep the fields or use `feincms3-meta
                                                 <https://github.com/matthiask/feincms3-meta>`__
``_content_title``, ``_page_title``              keep the fields and the ``content_title`` and
                                                 ``page_title`` properties
``publication_date``, ``publication_end_date``   no equivalent; keep the fields and filter
                                                 in your queryset if you need them
``_ct_inventory``, ``navigation_extension``      no equivalent; drop
================================================ =====================================================

Check for duplicate URLs before adding the unique constraint:

.. code-block:: sql

    SELECT _cached_url, COUNT(*) FROM page_page GROUP BY 1 HAVING COUNT(*) > 1;

``MENUS`` may start with an empty value, so that new pages aren't added to a
menu by default:

.. code-block:: python

    MENUS = [
        ("", _("Not in a menu")),
        ("default", _("Default")),
        ("meta", _("Meta")),
        ("footer", _("Footer")),
    ]

Write the first migration by hand: rename the fields which only changed their
name, add the new fields, and fill them in a data migration while the old
fields still exist. Afterwards, switch to the final model and let
``makemigrations`` generate the migration removing the old fields:

.. code-block:: python

    def forwards(apps, schema_editor):
        Page = apps.get_model("cms", "Page")
        Application = apps.get_model("cms", "Application")

        applications = {app.parent_id: app.urlconf_path for app in Application.objects.all()}
        positions = defaultdict(int)
        # Pages ordered like FeinCMS ordered them
        for page in Page.objects.order_by("tree_id", "lft"):
            positions[page.parent_id] += 10
            page.position = positions[page.parent_id]
            page.static_path = bool(page.override_url)
            if page_type := applications.get(page.id):
                page.page_type = page.app_namespace = page_type
            else:
                page.page_type = page.template_key
            page.menu = page.navigation_group if page.in_navigation else ""
            if match := re.fullmatch(r"page\.page:(\d+)", page.redirect_to):
                page.redirect_to_page_id = int(match[1])
            else:
                page.redirect_to_url = page.redirect_to
            page.save()


    class Migration(migrations.Migration):
        dependencies = [("cms", "0002_initial")]

        operations = [
            migrations.RenameField("page", "active", "is_active"),
            migrations.RenameField("page", "_cached_url", "path"),
            migrations.RenameField("page", "language", "language_code"),
            migrations.AddField(
                "page",
                "position",
                models.PositiveIntegerField(db_index=True, default=0),
                preserve_default=False,
            ),
            migrations.AddField(
                "page", "static_path", models.BooleanField(default=False)
            ),
            # ... page_type, app_namespace, menu, redirect_to_url,
            # redirect_to_page
            migrations.RunPython(forwards, migrations.RunPython.noop),
        ]

The paths FeinCMS generated (the parent's path plus the slug, or the override
URL) are the same paths feincms3 generates. Using ``tree_id`` and ``lft`` for
the position keeps the order of root pages and siblings. The `guide for
migrating from django-mptt
<https://django-tree-queries.readthedocs.io/en/latest/#migrating-from-django-mptt>`__
in the django-tree-queries documentation has more details.

The system checks of :class:`~feincms3.mixins.LanguageAndTranslationOfMixin`
recommend a ``unique_together`` constraint on ``language_code`` and
``translation_of``; check for duplicates and add it in another migration.

The page view, URLconf, navigation and anything else which still depends on
FeinCMS' page model have to be replaced in the same deployment too, see
:ref:`build-your-cms`. ``feincms_nav feincms_page level=2 group="meta"`` for
example becomes the active children of the root of the current page's tree
which are in the ``meta`` menu:

.. code-block:: python

    @register.simple_tag(takes_context=True)
    def menu(context, menu):
        page = context["page"]
        return Page.objects.active().filter(parent=page.tree_path[0], menu=menu)

The admin switches from django-mptt's ``DraggableMPTTAdmin`` to
:class:`feincms3.admin.TreeAdmin`. Its ``list_display`` contains the columns
for collapsing subtrees and for moving pages and the indented title, keep
those. Older versions of feincms3 don't include ``"collapse_column"``; add it
yourself there and set ``list_display_links = ["indented_title"]``, otherwise
the collapse column becomes the link to the change form:

.. code-block:: python

    from content_editor.admin import ContentEditor
    from feincms3.admin import TreeAdmin

    @admin.register(models.Page)
    class PageAdmin(ContentEditor, TreeAdmin):
        list_display = [*TreeAdmin.list_display, "is_active", "menu", "page_type"]
        ...

Once that's done, ``db_table`` can be removed too if you want; Django then
renames the table to ``cms_page``.


.. _migrating-from-feincms-other-base-models:

Other base models
~~~~~~~~~~~~~~~~~

Blog entries of feincms-elephantblog, translations built with
``create_base_model(Translation(...))`` and other base models are migrated
the same way as the page model: plugins on the content type tables, the
content editor, feincms3 rendering, and finally a model of your own on the
existing table.

- Models living in one of your own apps keep their app label. Removing
  ``create_base_model()`` from the bases and handing the tables over to the
  plugins (see above) is enough; regions are defined using a ``regions`` list
  of :class:`content_editor.models.Region` instances.
- Models of third party apps such as elephantblog's ``Entry``, ``Category``
  and ``CategoryTranslation`` get a new home in an app of your own, with
  ``db_table`` set to the existing tables, including the many-to-many tables
  (``db_table`` on the ``ManyToManyField``). The fields added by elephantblog's
  extensions become normal fields. The views are short and easy to port;
  elephantblog's are based on Django's generic date views.
- ``feincms.translations`` has to be replaced by a few lines of your own; the
  ``translation`` property, the ``Translation()`` base class factory and the
  ``admin_translationinline`` helper are the parts used most often.


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


.. _migrating-from-feincms-verifying:

Verifying the migration
~~~~~~~~~~~~~~~~~~~~~~~

The goal of each step is that the site doesn't change for visitors. That makes
it easy to verify: fetch every URL of the site before and after each step
using a copy of the production database and compare the responses. Collect
the URLs while FeinCMS is still installed, for example the paths of all
active pages, the URLs of all objects shown by apps, archive pages, feeds,
the sitemap and a few URLs which should return 404:

.. code-block:: python

    # ./manage.py shell < snapshot.py
    import hashlib, json, os, pathlib, re
    from django.test import Client

    out = pathlib.Path("snapshots") / os.environ["SNAPSHOT"]
    out.mkdir(parents=True, exist_ok=True)
    client = Client()
    for url in json.loads(pathlib.Path("urls.json").read_text()):
        response = client.get(url)
        body = response.content.decode()
        # Ignore whitespace changes and CSRF tokens
        body = re.sub(r"\s+", " ", body).replace("> <", "><").replace("><", ">\n<")
        body = re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "", body)
        name = hashlib.sha1(url.encode()).hexdigest()
        (out / name).write_text(
            f"{url}\n{response.status_code} {response.get('Location', '')}\n{body}"
        )

``diff -r snapshots/before snapshots/after`` shows every change, and the
output is usually short enough to look at each difference. Use a dummy cache
backend while taking snapshots.

Saving a page, a blog entry etc. in the admin without changing anything
should not change any rows either. Comparing ``pg_dump --data-only`` output
of the affected tables before and after saving catches problems such as
plugins losing their region or rich text being cleansed differently.

Finally, compare the schema of the production database with the schema of a
database created from scratch with the new migrations. Compare the
structure, not the names: columns with their types and nullability, indexes
as the list of columns they cover, foreign keys as the column and the
referenced table, and check and unique constraints by their definition. On
PostgreSQL, ``information_schema.columns``, ``pg_index`` and
``pg_constraint`` contain everything needed. Tables which only exist in the
production database are left over from removed apps and content types
without any rows and can be dropped once the migration is done.
