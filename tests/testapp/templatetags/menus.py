from collections import defaultdict

from django import template
from django.db.models import Q
from django.utils.translation import get_language

from testapp.models import Page


register = template.Library()


@register.simple_tag
def menus():
    menus = defaultdict(list)
    pages = (
        Page.objects.with_tree_fields()
        .filter(Q(is_active=True), Q(language_code=get_language()), ~Q(menu=""))
        .extra(where=["tree_depth BETWEEN 1 AND 2"])
    )
    for page in pages:
        menus[page.menu].append(page)
    return menus


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
