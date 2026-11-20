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

    # Inside a view or middleware:
    page = ...
    if url := page.get_redirect_url():
        return HttpResponseRedirect(url)
    # Default rendering continues here.

If you're using :ref:`ref-root` you can decorate your handler with
``add_redirect_handler``.


Automatic redirects for moved objects
-------------------------------------

Moving a page or changing its slug changes its URL and the URLs of all its
descendants. :mod:`feincms3.redirects` remembers the URLs of objects and
redirects visitors and search engines from old URLs to the current ones. It
works for any model with a ``get_absolute_url()`` method, not just for pages.

Add the app and its middleware to your settings. The app label is
``feincms3_redirects``. The middleware has to be added *before* the page
middleware so that pages are found first; redirects are only used for
requests which would result in a 404 response otherwise:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "feincms3.redirects",
    ]

    MIDDLEWARE = [
        ...
        "feincms3.redirects.middleware.redirects_middleware",
        "app.pages.middleware.page_if_404_middleware",
    ]

Register the models whose URLs should be recorded, e.g. at the bottom of your
``models.py``:

.. code-block:: python

    from feincms3 import redirects

    redirects.register(Page, queryset=Page.objects.active())
    redirects.register(Article, queryset=lambda request: Article.objects.published())

The current URL of an object is recorded each time it is saved. Saving a page
also saves its descendants, so their URLs are recorded too. An object's old
URLs keep pointing to it, so requests to them are redirected to the object's
current URL using a permanent redirect. This also works when an URL changes
without the object being saved, e.g. articles of an app whose page has been
moved. The query string of the request is kept.

The ``queryset`` determines which objects may be redirected to, e.g. only
active pages. It may also be a callable accepting the request. Old URLs of
inactive or deleted objects result in a 404 response.

Run ``./manage.py record_redirects`` once after adding the app to record the
current URLs of existing objects.

.. note::

   On sites with several hosts, e.g. when using `feincms3-sites
   <https://github.com/matthiask/feincms3-sites>`__, pass ``get_host`` so
   that URLs are only redirected on the host they belong to:

   .. code-block:: python

       redirects.register(
           Page,
           queryset=lambda request: Page.objects.active().filter(site=request.site),
           get_host=lambda page: page.site.host,
       )

   Redirects without a host are used for all hosts. Recording URLs uses an
   upsert query (``bulk_create(update_conflicts=True)``), which isn't
   supported on MySQL. ``AbstractPage`` doesn't support MySQL either.
