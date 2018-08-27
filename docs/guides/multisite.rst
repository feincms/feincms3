Multisite setup
===============

`feincms3-sites
<https://github.com/matthiask/feincms3-sites>`__'s documentation:

feincms3-sites allows running a feincms3 site on several domains, with
separate page trees etc. on each (if so desired).

The default behavior allows to match a single host. The advanced options
fieldset in the administration panel allows specifying your own regex,
which is matched against the host. There can be at most one default
site.


Installation and usage
~~~~~~~~~~~~~~~~~~~~~~

- ``pip install feincms3-sites``
- Your page model should extend ``feincms3_sites.models.AbstractPage``
  instead of ``feincms3.pages.AbstractPage``. The only difference is
  that our ``AbstractPage`` has an additional ``site`` foreign key, and
  path uniqueness is enforced per-site.
- Add ``feincms3_sites`` to ``INSTALLED_APPS`` and run ``./manage.py
  migrate``
- If you're using feincms3 apps currently, replace
  ``feincms3.apps.apps_middleware`` with
  ``feincms3_sites.middleware.apps_middleware`` in your ``MIDDLEWARE``.
  Otherwise, you may want to add
  ``feincms3_sites.middleware.site_middleware`` near the top. Both
  middleware functions either set ``request.site`` to the current site
  instance or raise a ``Http404``  exception.
- Uses of ``apps_urlconf()`` in your own code (improbable!) have to be
  replaced by ``feincms3_sites.middleware.apps_urlconf_for_site(site)``.
- ``Page.objects.active(site)`` is changed to require a ``site``
  argument. This causes a bit of code churn in template tags etc., but
  also ensures that filtering by site isn't easily forgotten.
- If you want to automatically redirect requests to the current site,
  insert ``feincms3_sites.middleware.redirect_to_site_middleware`` after
  one of the other middleware referenced above. You may also set
  ``SecurityMiddleware``'s ``SECURE_SSL_REDIRECT = True`` to enforce
  SSL. In this case, insert ``redirect_to_site_middleware`` before the
  ``SecurityMiddleware``.
- It is possible to define a default language per site. If this sounds
  useful to you, replace ``django.middleware.locale.LocaleMiddleware``
  with ``feincms3_sites.middleware.default_language_middleware``.


Accessing the site without a request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It might be useful under some circumstances to access a *current site*
instance (whatever that may be) without passing the request everywhere,
similar to ``django.utils.translation.get_language``. This can be easily
achieved by writing your own middleware module. I do not want to
encourage such usage (I find the explicitness of passing the request or
the site desirable, even though it is sometimes annoying), but since
there is no question that it might be useful it still is documented
here:

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
