"""
The template tags in ``feincms3_pages`` are mainly concerned with rendering
menus.

An example where there is a root node per language (that is, a MPTT ``tree_id``
per language), and the first two navigation levels should be rendered follows.
This example showcases all template tags in this template tag library::

    {% load feincms3_pages %}

    <nav class="nav-main">
    {% menu "main" level=1 depth=2 tree_id=page.tree_id as pages %}
    {% for main, children in pages|group_by_tree %}

      {% is_descendant_of page main include_self=True as active %}
      <a {% if active %}class="active"{% endif %}
         href="{{ main.get_absolute_url }}">{{ main.title }}</a>

        {% if children %}
        <nav>
          {% for child in children %}
            {% is_descendant_of page child include_self=True as active %}
            <a {% if active %}class="active"{% endif %}
               href="{{ child.get_absolute_url }}">{{ child.title }}</a>
          {% endfor %}
        </nav>
      {% endif %}

    {% endfor %}
    </nav>
"""

from django import template


register = template.Library()


@register.filter
def group_by_tree(iterable):
    """
    Given a list of MPTT objects in tree order, generate pairs consisting of
    the parents and their descendants in a list.
    """

    parent = None
    children = []
    level = -1

    for element in iterable:
        if parent is None or element.level == level:
            if parent:
                yield parent, children
                parent = None
                children = []

            parent = element
            level = element.level
        else:
            children.append(element)

    if parent:
        yield parent, children


@register.simple_tag
def is_descendant_of(node1, node2, include_self=False):
    """
    Return whether the first argument is a descendant of the second argument.

    If using this tag to determine whether menu entries should be active or
    not ``include_self=True`` should be specified.
    """
    return node1.is_descendant_of(node2, include_self=include_self)


@register.simple_tag(takes_context=True)
def menu(context, menu, *, level=0, depth=1, **kwargs):
    """menu(menu, level=0, depth=1, **kwargs)
    This tag expects the ``page`` variable to contain the page we're on
    currently. The active pages are fetched using ``.objects.active()`` and
    filtered further according to the arguments passed to the tag. This tag
    depends on :class:`~feincms3.mixins.MenuMixin` and on a ``page`` context
    variable which must be an instance of the pages model.

    **Note**: MPTT levels are zero-based.

    The default is to return all root nodes from the matching ``menu``.
    """

    # TODO we need some better way to identify the page class.
    return context['page'].__class__.objects.active().filter(
        menu=menu,
        level__range=[level, level + depth - 1],
        **kwargs
    )
