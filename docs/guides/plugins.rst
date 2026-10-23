.. _plugins:

Writing plugins
===============

Plugins for a given model extend an abstract base class created by
django-content-editor's ``create_plugin_base`` function. A minimal
example follows here:

.. code-block:: python

    from content_editor import Region, create_plugin_base

    class Article(models.Model):
        regions = [Region(...)]
        title = models.CharField(...)

    ArticlePlugin = create_plugin_base(Article)

    class Text(ArticlePlugin):
        text = models.TextField()

    class Download(ArticlePlugin):
        download = models.FileField(upload_to="downloads/")
        caption = models.CharField(blank=True, max_length=200)

The ``create_plugin_base`` creates an abstract model with the following
fields and methods in the example above:

- ``parent``: A foreign key to ``Article``.
- ``region``: A char field ready for holding the region's key it belongs
  to.
- ``ordering``: An integer field which orders the list of content
  elements. The value of the ordering field should be treated as opaque
  in that you should not depend on exact values and gaps in the ordering
  field values.
- ``get_queryset``: A classmethod without arguments which is used to
  fetch a queryset of plugin instances. If you have a plugin with a
  foreign key (not to ``parent`` but to other instances) it would
  probably be a really good idea to override this classmethod with one
  that adds a ``select_related()`` call.

.. admonition:: Historical note

   FeinCMS 1's ``create_content_type`` method could not be avoided
   because it added the dynamically created (concrete!) model to a few
   lists for bookkeeping.

   By contrast using ``create_plugin_base`` is not strictly necessary.
   However, django-content-editor and by extension feincms3 assume a few
   properties which you'd have to replicate by hand such as
   the model fields, the ``related_name`` pattern etc.


.. _richtext-prose-editor:

Rich text
~~~~~~~~~

Don't use the bundled :class:`feincms3.plugins.richtext.RichText` model: Its
``text`` field is the deprecated
:class:`~feincms3.inline_ckeditor.InlineCKEditorField` which uses CKEditor 4,
which has reached its end of life. The field hasn't been replaced yet because
other editors only accept a stricter subset of HTML, which wouldn't be
backwards compatible with existing content.

Define your own rich text plugin using `django-prose-editor
<https://github.com/matthiask/django-prose-editor>`__ instead. Install it
with ``pip install django-prose-editor[sanitize]`` and add
``"django_prose_editor"`` to ``INSTALLED_APPS``. The editor only offers the
configured extensions, and ``sanitize=True`` removes all HTML which these
extensions do not produce:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from django_prose_editor.fields import ProseEditorField

    class RichText(PagePlugin):
        text = ProseEditorField(
            _("text"),
            extensions={
                "Bold": True,
                "Italic": True,
                "Heading": {"levels": [2, 3]},
                "BulletList": True,
                "OrderedList": True,
                "Link": True,
            },
            sanitize=True,
        )

        def __str__(self):
            return self.get_text_excerpt()

``ProseEditorField`` adds the ``get_text_excerpt()`` method. The admin inline
(``plugins.richtext.RichTextInline``) and the renderer
(``plugins.richtext.render_richtext``) of the bundled plugin can still be
used. Switching an existing project requires a migration. Existing content containing HTML
which the configured extensions don't support loses that markup when it is
edited and saved the next time.
