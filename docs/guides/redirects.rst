.. _redirects:

Redirects
=========

The :class:`feincms3.mixins.RedirectMixin` allows redirecting pages to
other pages or arbitrary URLs. Inheriting the mixin adds two fields,
the char field ``redirect_to_url`` and the self-referencing foreign key
``redirect_to_page``:

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
        if page.get_redirect_url():
            return redirect(page.get_redirect_url())
        # Default rendering continues here.
