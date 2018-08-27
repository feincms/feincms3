.. _redirects:

Redirects
=========

The ``RedirectMixin`` allows redirecting pages to other pages or arbitrary
URLs:

.. code-block:: python

    from feincms3.mixins import RedirectMixin
    from feincms3.pages import AbstractPage

    class Page(RedirectMixin, AbstractPage):
        pass

At most one of ``redirect_to_url`` or ``redirect_to_page`` may be set,
never both at the same time. The actual redirecting is not provided. This
has to be implemented in the page view:

.. code-block:: python

    from django.shortcuts import redirect

    def page_detail(request, path):
        page = ...
        if page.redirect_to_url or page.redirect_to_page:
            return redirect(page.redirect_to_url or page.redirect_to_page)
        # Default rendering continues here.
