from django.shortcuts import render
from testapp.models import Page
from testapp.renderer import page_context

from feincms3.root.middleware import add_redirect_handler, create_page_if_404_middleware


@add_redirect_handler
def handler(request, page):
    return render(request, page.type.template_name, page_context(request, page=page))


page_if_404_middleware = create_page_if_404_middleware(
    queryset=Page.objects.active(),
    handler=handler,
    language_code_redirect=True,
)
