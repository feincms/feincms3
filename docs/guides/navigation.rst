.. _navigation:

Navigation generation recipes
=============================

This guide provides a few examples and snippets for generating the
navigation for a site dynamically.

feincms3's :class:`~feincms3.pages.AbstractPage` model inherits the
methods of ``tree_queries.models.TreeNode``, notably
``page.ancestors()`` and ``page.descendants()``. These methods and the
attributes added by django-tree-queries, ``tree_path`` and
``tree_depth`` will prove useful for generating navigations.

feincms3 does not have a concrete page model and does not provide any
tags to fetch page instances from the template. You'll have to provide
the context variables yourself, preferrably by writing your own template
tags.

This guide assumes that the concrete page model is available at
``app.pages.models.Page``, and that you'll add a ``menus`` template tag
library somewhere where it may be used by Django.


A simple main menu
~~~~~~~~~~~~~~~~~~

Add the following template tag to the ``menus.py`` file:

.. code-block:: python

    from django import template
    from app.pages.models import Page

    register = template.Library()

    @register.simple_tag
    def main_menu():
        return Page.objects.with_tree_fields().active().filter(parent=None)

The template (where the ``page`` variable holds the current page)::

    {% load menus %}
    {% main_menu as menu %}
    <nav class="main-menu">
    {% for p in menu %}
      <a
        {% if p.id in page.tree_path %}class="active"{% endif %}
        href="{{ p.get_absolute_url }}">{{ p.title }}</a>
    {% endfor %}
    </nav>

The ``tree_path`` attribute contains the list of all ancestors' primary
keys including the key of the node itself. The ``active`` class is added
to all menu entries that are either an ancestor of the current page or
are the current page itself.


Breadcrumbs
~~~~~~~~~~~

Breadcrumbs for the current page are generated easily, without the help
of a template tag. Ancestors are returned starting from the root node
(again, the ``page`` variable holds the current page)::

    <nav class="breadcrumbs">
    {% for ancestor in page.ancestors %}
      {% if forloop.last %}
        {{ ancestor.title }}
      {% else %}
        <a href="{{ ancestor.get_absolute_url }}">{{ ancestor.title }}</a>
        &gt;
      {% endif %}
    {% endfor %}
    </nav>


Main menu with two levels and meta navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this example, the page class should also inherit the
:class:`feincms3.mixins.MenuMixin` with a ``MENUS`` value as follows:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from feincms3.mixins import MenuMixin
    from feincms3.pages import AbstractPage

    class Page(MenuMixin, ..., AbstractPage):
        MENUS = (
            ('main', _('main navigation')),
            ('meta', _('meta navigation')),
        )

Let's write a template tag which returns all required nodes at once:

.. code-block:: python

    from collections import defaultdict
    from django import template
    from app.pages.models import Page

    register = template.Library()

    @register.simple_tag
    def all_menus():
        menus = defaultdict(list)
        pages = Page.objects.with_tree_fields().active().exclude(
            menu=""
        ).extra(
            where=["tree_depth<=1"]
        )
        for page in pages:
            menus[page.menu].append(page)
        return menus

The template tag removes all pages that aren't added to a menu and
filters for the first two levels in the tree. ``tree_depth`` is only
available as an ``.extra()`` field, so you cannot use ``.filter()`` to
do this.

Next, let's add a template filter which returns parents bundled together
with their children:

.. code-block:: python

    @register.filter
    def group_by_tree(iterable):
        parent = None
        children = []
        depth = -1

        for element in iterable:
            if parent is None or element.tree_depth == depth:
                if parent:
                    yield parent, children
                    parent = None
                    children = []

                parent = element
                depth = element.tree_depth
            else:
                children.append(element)

        if parent:
            yield parent, children

Now, a possible use of those two tags in the template looks as follows::

    {% load menus %}
    {% all_menus as menus %}

    <nav class="nav-main">
    {% for main, children in menus.main|group_by_tree %}
      <a
        {% if page and main.id in page.tree_path %}class="active"{% endif %}
        href="{{ main.get_absolute_url }}">{{ main.title }}</a>
        {% if children %}
        <nav>
          {% for child in children %}
            <a
              {% if page and child.id in page.tree_path %}class="active"{% endif %}
              href="{{ child.get_absolute_url }}">{{ child.title }}</a>
          {% endfor %}
        </nav>
      {% endif %}
    {% endfor %}
    </nav>

    {# ... and an analogous block for the meta menu, maybe without the children loop #}
