Regions (``feincms3.regions``)
==============================

What is a Region?
~~~~~~~~~~~~~~~~~

A **Region** is a named area within a page or content item where plugins (content blocks) can be placed and organized. Regions define the structure and layout of your content, allowing editors to add different types of content (text, images, videos, etc.) to specific areas of a page.

Think of regions as placeholder zones in your templates. For example, a typical page might have:

- A ``"main"`` region for the primary content
- A ``"sidebar"`` region for secondary information
- A ``"footer"`` region for additional content

Each region is defined with a unique key and a human-readable title:

.. code-block:: python

    from content_editor.models import Region

    regions = [
        Region(key="main", title=_("Main content")),
        Region(key="sidebar", title=_("Sidebar"), inherited=True),
    ]

Regions can be marked as ``inherited``, meaning that if a page doesn't have content in that region, it will inherit content from its parent pages in the tree structure.

In templates, you render the content of a region using the ``render_region`` template tag:

.. code-block:: html+django

    {% load feincms3 %}

    <main>
        {% render_region page_regions "main" %}
    </main>
    <aside>
        {% render_region page_regions "sidebar" %}
    </aside>

For more detailed information about working with regions and templates, see the :doc:`../guides/templates-and-regions` guide.

API Reference
~~~~~~~~~~~~~

.. automodule:: feincms3.regions
   :members:

.. autofunction:: feincms3.templatetags.feincms3.render_region
