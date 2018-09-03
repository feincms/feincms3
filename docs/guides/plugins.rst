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

.. note::
   FeinCMS 1's ``create_content_type`` method could not be avoided
   because it added the dynamically created (concrete!) model to a few
   lists for bookkeeping.

   By contrast using ``create_plugin_base`` is not strictly necessary.
   However, django-content-editor and by extension feincms3 assume a few
   properties which you'd have to replicate by hand.

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
