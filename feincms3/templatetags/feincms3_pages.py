from __future__ import absolute_import, unicode_literals

from django import template


register = template.Library()


@register.filter
def group_by_tree(iterable):
    """
    Group pages of two navigation levels. Usage example::

        {% load feincms3_pages %}

        <ul class="nav-main">
          {% menu "main" level=1 depth=2 tree_id=page.tree_id as pages %}
          {% for main, children in pages|group_by_tree %}
            {% is_descendant_of page main include_self=True as active %}
            <li {% if active %}class="active"{% endif %}>
              <a href="{{ main.get_absolute_url }}"{{ main.title }}</a>
              {% if children %}
                <ul>
                  {% for child in children %}
                    {% is_descendant_of page child include_self=True as active %}
                    <li {% if active %}class="active"{% endif %}>
                      <a href="{{ child.get_absolute_url }}">{{ child.title }}</a>
                    </li>
                  {% endfor %}
                </ul>
              {% endif %}
            </li>
          {% endfor %}
        </ul>
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
    Returns whether the first argument is a descendant of the second argument.

    The recommended usage is documented below for the {% menu %} template tag.
    """
    return node1.is_descendant_of(node2, include_self=include_self)


@register.simple_tag
# def menu(menu, *, level=0, depth=1, **kwargs):
def menu(menu, level=0, depth=1, **kwargs):  # PY2 :-(
    return Page.objects.active().filter(
        menu=menu,
        level__range=[level, level + depth - 1],
        **kwargs
    )
