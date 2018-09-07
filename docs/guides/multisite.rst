Multisite setup
===============

feincms3-sites allows running a feincms3 site on several domains, with
separate page trees etc. on each (if so desired).

Installation and configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the package:

.. code-block:: shell

    pip install feincms3-sites

Inherit feincms3-sites's page model instead of the default feincms3
abstract page.  The only difference is that this ``AbstractPage`` model
has an additional ``site`` foreign key, and path uniqueness is enforced
per-site:

.. code-block:: python

    from feincms3_sites.models import AbstractPage

    class Page(..., AbstractPage):
        pass


Add ``feincms3_sites`` to ``INSTALLED_APPS`` and run migrations
afterwards:

.. code-block:: python

    INSTALLED_APPS.append("feincms3_sites")

.. code-block:: shell

    ./manage.py migrate

If you're using feincms3 apps currently, replace
``feincms3.apps.apps_middleware`` with
``feincms3_sites.middleware.apps_middleware`` in your ``MIDDLEWARE``.
Otherwise, you may want to add
``feincms3_sites.middleware.site_middleware`` near the top. Both
middleware functions either set ``request.site`` to the current
``feincms3_sites.models.Site`` instance or raise a ``Http404``
exception.

The default behavior allows matching a single host. The advanced options
fieldset in the administration panel of feincms3-sites allows specifying
your own regex, allowing matching several hostnames. In this case you
may also want to add
``feincms3_sites.middleware.redirect_to_site_middleware`` after the
middleware mentioned above. If you're also using the
``SECURE_SSL_REDIRECT`` of Django's own ``SecurityMiddleware`` you have
to add the ``redirect_to_site_middleware`` *before*
``SecurityMiddleware``.

It is also possible to specify a default site. At most one site is
allowed to be the default site. In this case, when no site's regex
matches, the default site is selected instead as a fallback.


Multisite support throughout your code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most visible change is that calls to ``Page.objects.active()`` have
to be replaced by ``Page.objects.active(request.site)``. This creates a
bit of churn in your code but also ensures that filtering by the current
site isn't forgotten.

Uses of ``apps_urlconf()`` in your own code (improbable!) have to be
replaced by ``feincms3_sites.middleware.apps_urlconf_for_site(site)``.


Default languages for sites
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some configurations it may be useful to specify a default language
per site. In this case you should replace
``django.middleware.locale.LocaleMiddleware`` with
``feincms3_sites.middleware.default_language_middleware``. This
middleware has to be placed after the ``site_middleware`` or
``apps_middleware``.


Accessing the site without a request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It might be useful under some circumstances to access a *current site*
instance without passing the request everywhere, similar to
``django.utils.translation.get_language``. This can be easily achieved
by writing your own middleware module. I do not want to encourage such
usage (I find the explicitness of passing the request or the site
desirable, even though it is sometimes annoying), but since there is no
question that it might be useful it still is documented here:

.. code-block:: python

    from contextlib import contextmanager
    from threading import local

    _local = local()

    @contextmanager
    def set_current_site(site):
        outer = current_site()
        _local.site = site
        yield
        _local.site = outer

    def current_site():
        # Return the default site if _local.site is None?
        return getattr(_local, 'site', None)

    # Add this middleware after site_middleware or apps_middleware
    def current_site_middleware(get_response):
        def middleware(request):
            with set_current_site(request.site):
                return get_response(request)
        return middleware
