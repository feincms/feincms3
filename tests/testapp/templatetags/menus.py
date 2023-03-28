from collections import defaultdict

from django import template
from django.db.models import Q
from django.utils.translation import get_language

from testapp.models import Page


register = template.Library()


@register.simple_tag
def menus():
    menus = defaultdict(list)
    pages = Page.objects.filter(
        Q(is_active=True), Q(language_code=get_language()), ~Q(menu="")
    ).extra(where=["tree_depth BETWEEN 1 AND 2"])
    for page in pages:
        menus[page.menu.replace("-", "_")].append(page)
    return menus


@register.filter
def group_by_parent(iterable):
    parent = None
    children = []

    for element in iterable:
        if parent is None or element.tree_depth == parent.tree_depth:
            if parent:
                yield parent, children
                parent = None
                children = []

            parent = element
        else:
            children.append(element)

    if parent:
        yield parent, children


@register.tag
def ifactive(parser, token):
    try:
        tag_name, page = token.split_contents()
    except ValueError as exc:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        ) from exc

    nodelist = parser.parse(("endifactive",))
    parser.delete_first_token()
    return IfActiveNode(page, nodelist)


class IfActiveNode(template.Node):
    def __init__(self, page, nodelist):
        self.page = template.Variable(page)
        self.nodelist = nodelist

    def render(self, context):
        page = self.page.resolve(context)
        current_page = context.get("page")
        if not current_page or page.id not in current_page.tree_path:
            return ""
        return self.nodelist.render(context)
