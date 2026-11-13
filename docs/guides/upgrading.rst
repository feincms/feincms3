.. _upgrading:

================
Upgrading to 7.0
================

This page is a checklist for upgrading a project to feincms3 7.0. It is
written so that it can be followed step by step, also by a coding agent.

feincms3 7.0 requires django-content-editor 10.0, which stores the nesting of
plugins explicitly and replaces closer-based sections with containers. Most of
the work happens there and is described in django-content-editor's
`upgrading guide
<https://django-content-editor.readthedocs.io/en/latest/upgrading.html>`__.
This page only covers what is specific to feincms3.


Overview
========

- **All projects** upgrade the packages and follow django-content-editor's
  upgrading guide (steps 1–2).
- **Projects using feincms3's renderer** may switch to django-content-editor's
  renderer if they don't use any of the deprecated APIs (step 3). This is
  optional, ``feincms3.renderer`` keeps working.
- **Projects using feincms3's rich text plugin** or CKEditor 4 fields replace
  them with django-prose-editor (step 4). This isn't required for 7.0, but
  these modules are deprecated and will be removed.
- Remove the remaining deprecated APIs and verify the upgrade (steps 5–6).

Steps 3 and 4 are independent of the content editor migration and of each
other; they can be done in separate changes.


1. Upgrade the packages
=======================

Upgrade the following packages at the same time:

- ``feincms3`` to 7.0 or better
- ``django-content-editor`` to 10.0 or better
- ``django-tree-queries`` to 0.28 or better


2. Upgrade django-content-editor
================================

Follow django-content-editor's `upgrading guide
<https://django-content-editor.readthedocs.io/en/latest/upgrading.html>`__.
All projects have to add the ``depth`` column to their plugin tables; projects
using closer-based sections additionally migrate their content to containers.

Notes for feincms3 projects:

- The region renderer moved to ``content_editor.renderer``.
  ``feincms3.renderer`` re-exports it, so existing imports keep working, and
  ``RegionRenderer`` now renders containers.
- ``RegionRenderer.render_section_plugins`` and
  ``RegionRenderer.register_section_close`` only exist on
  ``feincms3.renderer.RegionRenderer``. Keep importing the renderer from
  ``feincms3.renderer`` until the project has been migrated to containers.


3. Switch to django-content-editor's renderer (optional)
========================================================

``feincms3.renderer.RegionRenderer`` is a subclass of
``content_editor.renderer.RegionRenderer`` which only adds deprecated APIs.
Projects which don't use them can use django-content-editor's renderer
directly; the rendering doesn't change.

Check the prerequisites
-----------------------

The project mustn't use any of the following anymore:

- ``render_section_plugins`` and ``register_section_close`` (closer-based
  sections, see step 2)
- ``register_string_renderer``, ``register_template_renderer`` and
  ``render_plugin_in_context`` (use ``register`` with ``template_renderer``,
  and ``render_plugin`` instead)
- ``TemplatePluginRenderer`` (use ``RegionRenderer``)
- The ``handlers`` property of the renderer
- The ``feincms3.regions`` module (use ``RegionRenderer.regions_from_item``)

Find usages with::

    git grep -nE 'render_section_plugins|register_section_close|register_string_renderer|register_template_renderer|render_plugin_in_context|TemplatePluginRenderer|\.handlers\b|feincms3\.regions'

Replace or remove all usages first. Running the test suite with ``python -Wd``
shows ``DeprecationWarning`` messages for usages the search didn't find.

Replace the imports
-------------------

Import ``RegionRenderer``, ``template_renderer``, ``render_in_context``,
``default_context`` and ``PluginNotRegisteredError`` from
``content_editor.renderer`` instead of ``feincms3.renderer``:

.. code-block:: python

    # Before
    from feincms3.renderer import RegionRenderer, template_renderer

    # After
    from content_editor.renderer import RegionRenderer, template_renderer

Also change the base class of ``RegionRenderer`` subclasses. Rename usages of
``PluginNotRegistered``, which is a deprecated alias of
``PluginNotRegisteredError`` and only exists in ``feincms3.renderer``.

Afterwards, ``git grep -n feincms3.renderer`` shouldn't find anything.

Replace the template tag
------------------------

django-content-editor ships its own ``{% render_region %}`` tag, which works
the same as feincms3's:

.. code-block:: html+django

    {% load content_editor %}
    {% render_region regions "main" %}

Templates which also use feincms3's other tags (``{% reverse_app %}``,
``{% translations %}`` etc.) still need ``{% load feincms3 %}``. When a
template loads both libraries, the library loaded last provides
``{% render_region %}``; both tags do the same thing, so the order doesn't
matter.


4. Replace the rich text plugin
===============================

``feincms3.plugins.richtext`` and ``feincms3.inline_ckeditor`` use CKEditor 4,
which has reached its end of life; ``feincms3.plugins.old_richtext`` and
``feincms3.cleanse`` depend on django-ckeditor. All of them are deprecated.
Define a rich text plugin of your own using `django-prose-editor
<https://github.com/matthiask/django-prose-editor>`__ instead.

The text stays in the same column: ``InlineCKEditorField`` and
``ProseEditorField`` both act like a ``TextField`` in migrations. Replacing
``CleansedRichTextField`` (based on django-ckeditor's ``RichTextField``)
produces an ``AlterField`` operation which doesn't change the database. The
difference is the editor and the allowlist
of HTML elements which survive saving the plugin, so most of the work is
making sure that existing content survives.

Take inventory
--------------

Find the models, inlines and renderers using the deprecated modules::

    git grep -nE 'plugins\.richtext|plugins import (.*\b)?(old_)?richtext|old_richtext|InlineCKEditorField|CleansedRichTextField|feincms3\.cleanse|FEINCMS3_CKEDITOR_CONFIG|CKEDITOR_CONFIGS'

``./manage.py check`` reports models using ``InlineCKEditorField`` as
``feincms3.W007``.

Note the options passed to the fields (``config``, ``config_name``,
``cleanse``) and the HTML sanitizer configuration (``HTML_SANITIZERS``
setting), if the project changed the defaults. They determine which HTML
existing content may contain.

Install django-prose-editor
---------------------------

Install it with ``pip install django-prose-editor[sanitize]`` and add
``"django_prose_editor"`` to ``INSTALLED_APPS``.

Define the model
----------------

Replace the base class and the field, and keep the name of the model so that
the table stays the same. Define the extensions as a module level constant,
the content check and the data migration below use it too:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from django_prose_editor.fields import ProseEditorField

    # Matches the default configuration of the deprecated rich text plugin
    RICH_TEXT_EXTENSIONS = {
        "Heading": {"levels": [1, 2, 3]},
        "Bold": True,
        "Italic": True,
        "Subscript": True,
        "Superscript": True,
        "BulletList": True,
        "OrderedList": True,
        "ListItem": True,
        "Link": True,
        "HorizontalRule": True,
        "HardBreak": True,
    }


    # Before: class RichText(richtext.RichText, PagePlugin):
    class RichText(PagePlugin):
        text = ProseEditorField(
            _("text"),
            extensions=RICH_TEXT_EXTENSIONS,
            sanitize=True,
        )

        class Meta:
            verbose_name = _("rich text")
            verbose_name_plural = _("rich texts")

        def __str__(self):
            return self.get_text_excerpt()

The extensions above allow the same elements as the default configuration of
the deprecated plugins. Projects which changed the CKEditor or HTML sanitizer
configuration adapt the extensions accordingly; see django-prose-editor's
documentation for the available extensions. Don't forget ``ListItem`` when
using lists, and ``HardBreak`` for line breaks: elements without an extension
are removed.

The ``Meta`` class keeps the verbose names the deprecated abstract model
defined. Run ``./manage.py makemigrations``; it shouldn't detect any changes,
apart from the ``AlterField`` when replacing a ``CleansedRichTextField``. If it
does, compare the model with the previous definition.

Update the admin and the renderer
---------------------------------

.. code-block:: python

    # admin.py
    from content_editor.admin import ContentEditorInline

    inlines = [
        # Before: richtext.RichTextInline.create(models.RichText),
        ContentEditorInline.create(models.RichText, icon="notes"),
        ...
    ]

    # renderer.py
    from django.utils.html import mark_safe

    # Before: renderer.register(models.RichText, lambda plugin, context: richtext.render_richtext(plugin))
    renderer.register(models.RichText, lambda plugin, context: mark_safe(plugin.text))

Renderers using ``template_renderer`` and a template don't need changes.

Check existing content
----------------------

``sanitize=True`` only runs when a plugin is saved through a form, e.g. in the
admin. Existing content stays as it is until an editor saves it the next time,
then all HTML which the extensions don't produce is removed. With the
configuration above, this affects for example:

- ``name`` attributes of links (anchors created using CKEditor's "Anchor"
  button). The link itself is kept, the anchor stops working.
- Headings of levels the configuration doesn't allow; they become plain text.
- Elements which an extended HTML sanitizer configuration allowed, e.g.
  tables or ``class`` attributes.

Find the affected plugins before deploying, e.g. in ``./manage.py shell``:

.. code-block:: python

    from django_prose_editor.fields import create_sanitizer

    from app.pages.models import RICH_TEXT_EXTENSIONS, RichText

    sanitize = create_sanitizer(RICH_TEXT_EXTENSIONS)
    for plugin in RichText.objects.select_related("parent"):
        if sanitize(plugin.text) != plugin.text:
            print(plugin.pk, plugin.parent, plugin.text, sep="\n", end="\n\n")

Differences in whitespace or in the serialization of the same HTML (e.g.
``<br />`` vs. ``<br>``) are harmless. For the others, decide whether to add
extensions, to fix the content by hand, or to accept the change.

Optionally, sanitize all existing content in a data migration. The rendered
HTML then changes at deployment time, and not later when someone happens to
edit the plugin:

.. code-block:: python

    from django.db import migrations
    from django_prose_editor.fields import create_sanitizer

    # Copy the extensions instead of importing them if they may change later.
    from app.pages.models import RICH_TEXT_EXTENSIONS


    def forwards(apps, schema_editor):
        RichText = apps.get_model("pages", "RichText")
        sanitize = create_sanitizer(RICH_TEXT_EXTENSIONS)
        for plugin in RichText.objects.all():
            if (text := sanitize(plugin.text)) != plugin.text:
                plugin.text = text
                plugin.save(update_fields=["text"])


    class Migration(migrations.Migration):
        dependencies = [("pages", "00xx_previous")]
        operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

Back up the database first; the migration cannot be reversed.

Clean up
--------

Repeat the steps above for all models using the deprecated fields. Then
remove:

- The ``FEINCMS3_CKEDITOR_CONFIG`` setting.
- ``ckeditor`` from ``INSTALLED_APPS``, the ``CKEDITOR_CONFIGS`` setting and
  the django-ckeditor dependency, if the project used
  ``feincms3.plugins.old_richtext`` or ``feincms3.cleanse``.
- The ``HTML_SANITIZERS`` setting and the html-sanitizer dependency, if
  nothing else uses them.
- Project CSS and JavaScript customizing CKEditor.

Editors should know that the toolbar looks different, and that pasting
formatted text only keeps the formatting the extensions support.


5. Remove the remaining deprecated APIs
=======================================

- ``feincms3.admin.MoveForm`` and the ``<pk>/move/`` view of
  ``feincms3.admin.TreeAdmin`` are deprecated. The changelist uses the move
  controls of django-tree-queries' ``TreeAdmin``. Remove custom links to the
  move view, and override ``TreeAdmin.is_valid_move`` instead of customizing
  ``MoveForm`` to restrict moves.

Find usages with::

    git grep -nE 'MoveForm|/move/|move_view'


6. Verify
=========

- ``./manage.py check`` reports no ``feincms3.W007``, and none of the warnings
  and errors listed in django-content-editor's upgrading guide.
- ``./manage.py makemigrations --check`` reports no changes.
- The test suite passes without a ``DeprecationWarning`` from feincms3 or
  django-content-editor (``python -Wd``).
- Open content in the admin: the rich text editor works, and saving existing
  rich text plugins without changes doesn't change their content (unless you
  decided to accept that in step 4).
- Compare the rendered HTML with the HTML before the upgrade, as described in
  django-content-editor's upgrading guide.
