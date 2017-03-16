"""
The template tags in ``feincms3_pages`` are mainly concerned with rendering
menus.

An example where there is a root node per language, and the first two
navigation levels should be rendered follows.  This example showcases all
template tags in this template tag library::

    {% load feincms3_pages %}

    <nav class="nav-main">
    {% menu "main" level=1 depth=2 language_code=page.language_code as pages %}
    {% for main, children in pages|group_by_tree %}

      <a {% if page and main.id in page.cte_path %}class="active"{% endif %}
         href="{{ main.get_absolute_url }}">{{ main.title }}</a>

        {% if children %}
        <nav>
          {% for child in children %}
            <a {% if page and child.id in page.cte_path %}class="active"{% endif %}
               href="{{ child.get_absolute_url }}">{{ child.title }}</a>
          {% endfor %}
        </nav>
      {% endif %}

    {% endfor %}
    </nav>
"""

from django import template

from feincms3.mixins import MenuMixin
from feincms3.utils import concrete_model

register = template.Library()


@register.filter
def group_by_tree(iterable):
    """
    Given a list of pages in tree order, generate pairs consisting of the
    parents and their descendants in a list.
    """

    parent = None
    children = []
    depth = -1

    for element in iterable:
        if parent is None or element.depth == depth:
            if parent:
                yield parent, children
                parent = None
                children = []

            parent = element
            depth = element.depth
        else:
            children.append(element)

    if parent:
        yield parent, children


@register.simple_tag
# def menu(menu, *, level=0, depth=1, **kwargs):
def menu(menu, level=0, depth=1, **kwargs):
    """menu(menu, level=0, depth=1, **kwargs)
    This tag expects the ``page`` variable to contain the page we're on
    currently. The active pages are fetched using ``.objects.active()`` and
    filtered further according to the arguments passed to the tag. This tag
    depends on :class:`~feincms3.mixins.MenuMixin` and on a ``page`` context
    variable which must be an instance of the pages model.

    **Note**: MPTT levels are zero-based.

    The default is to return all root nodes from the matching ``menu``.
    """
    return concrete_model(MenuMixin).objects.active().filter(
        menu=menu,
        **kwargs
    ).extra(where=[
        'depth BETWEEN %d AND %d' % (level + 1, level + depth),
    ])
