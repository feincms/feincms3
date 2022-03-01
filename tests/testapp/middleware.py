from django.shortcuts import render
from testapp.models import Page
from testapp.renderer import renderer

from feincms3.incubator.root import add_redirect_handler, create_page_if_404_middleware
from feincms3.regions import Regions


def handle_template(request, page):
    return render(
        request,
        page.type.template_name,
        {
            "page": page,
            "regions": Regions.from_item(
                item=page, renderer=renderer, inherit_from=page.ancestors().reverse()
            ),
        },
    )


page_if_404_middleware = create_page_if_404_middleware(
    queryset=Page.objects.active(),
    handler=add_redirect_handler(handle_template),
    language_code_redirect=True,
)
