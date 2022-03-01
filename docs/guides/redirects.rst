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

    class Page(AbstractPage, RedirectMixin):
        pass

At most one of ``redirect_to_url`` or ``redirect_to_page`` may be set,
never both at the same time. The actual redirecting is not provided. This
has to be implemented in the page view:

.. code-block:: python

    from django.http import HttpResponseRedirect

    def page_detail(request, path):
        page = ...
        if url := page.get_redirect_url():
            return HttpResponseRedirect(url)
        # Default rendering continues here.
