URLs and views
==============

.. warning::
    As mentioned in :ref:`build-your-cms` the recommended way to render pages
    is using a middleware. It may be easier to use URLconf entries and views if
    you're integrating the CMS functionality into an existing site or when you
    want to use it only for a subtree. (A middleware may still be the way to go
    in this case.)

The default implementation of ``AbstractPage.get_absolute_url`` still expects
the following URLconf entries and falls back to returning the path prefixed by
the script prefix:

.. code-block:: python

    from django.shortcuts import redirect
    from django.urls import path

    from app.pages import views

    app_name = "pages"
    urlpatterns = [
        path("<path:path>/", views.page_detail, name="page"),
        path("", views.page_detail, name="root"),
    ]

Just to be on the safe side you may want to override ``get_absolute_url`` on
your own page class:

.. code-block:: python

    class Page(AbstractPage, ...):
        def get_absolute_url(self):
            if self.path == "/":
                return reverse("pages:root")
            return reverse("pages:page", kwargs={"path": self.path.strip("/")})

A simple view might look as follows (building on the functionality from the
introduction):

.. code-block:: python

    from django.shortcuts import get_object_or_404, render

    from app.pages.models import Page
    from app.pages.utils import page_context

    def page_detail(request, path=None):
        page = get_object_or_404(Page.objects.active(), path=f"/{path}/" if path else "/")
        return render(request, "pages/standard.html", page_context(request, page=page))
