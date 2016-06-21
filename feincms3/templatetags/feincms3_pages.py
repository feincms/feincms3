from __future__ import absolute_import, unicode_literals

from django import template

from app.pages.models import Page


register = template.Library()


@register.filter
def group_by_tree(iterable):
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
    return node1.is_descendant_of(node2, include_self=include_self)


@register.simple_tag
# def menu(menu, *, level=0, depth=1, **kwargs):
def menu(menu, level=0, depth=1, **kwargs):  # PY2 :-(
    return Page.objects.active().filter(
        menu=menu,
        level__range=[level, level + depth - 1],
        **kwargs
    )
