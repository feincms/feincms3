.. _multisite:

Multisite setup
===============

`feincms3-sites <https://github.com/matthiask/feincms3-sites>`__ allows running
a feincms3 site on several domains, with separate page trees etc. on each (if
so desired). The same Django installation can serve several domains with
different content without having to start a Django server per site as you'd
have to if you were using ``django.contrib.sites``. This also means that
feincms3-sites isn't compatible with ``django.contrib.sites`` -- you have to
use one or the other.

.. note::
   The simpler case of having exactly one site per language and one language
   per site is better supported by `feincms3-language-sites
   <https://github.com/matthiask/feincms3-language-sites>`__.


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

    class Page(AbstractPage, ...):
        pass


Add ``FEINCMS3_SITES_SITE_MODEL = "feincms3_sites.Site"`` to
your ``settings``.

Add ``feincms3_sites`` to ``INSTALLED_APPS`` and run migrations
afterwards:

.. code-block:: python

    INSTALLED_APPS.append("feincms3_sites")
    FEINCMS3_SITES_SITE_MODEL = "feincms3_sites.Site"

.. code-block:: shell

    ./manage.py migrate

Add ``feincms3_sites.middleware.site_middleware`` near the top of your
``MIDDLEWARE`` setting, in any case before
``feincms3.applications.apps_middleware`` if you're using it. The middleware
either sets ``request.site`` to the current
``feincms3_sites.models.Site`` instance or raises a ``Http404``
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

It is also possible to specify a default site.  In this case, when no
site's regex matches, the default site is selected instead as a
fallback. The code does not prevent you from setting more than one site
as the default but sites are deterministically ordered so the same site
will always be selected.


Multisite support throughout your code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since feincms3-sites 0.6 a contextvar automatically provides the current
site when inside ``site_middleware``. The default implementation of
``Page.objects.active()`` filters by the current site. When you're
running queries on pages outside of a middleware you'll have to use the
contextvar facility yourself by running your code inside a ``with
feincms3_sites.middleware.set_current_site(site):`` block.


Default languages for sites
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some configurations it may be useful to specify a default language
per site. In this case you should replace
``django.middleware.locale.LocaleMiddleware`` with
``feincms3_sites.middleware.default_language_middleware``. This
middleware has to be placed after the ``site_middleware``.
