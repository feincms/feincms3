.. _apps-introduction:

Introduction to apps
====================

Apps are defined by a list of URL patterns specific to this app. A simple
contact form would probably only have a single URLconf entry (``r'^$'``), the
news app would at least have two entries (the archive and the detail URL).

The activation of apps happens through a dynamically created URLconf
module (probably the trickiest code in all of feincms3,
:func:`~feincms3.apps.apps_urlconf`). The
:class:`~feincms3.apps.apps_middleware` assigns the module to
``request.urlconf`` which ensures that apps are available for resolving
and URL reversing. No page code runs at all, control is directly passed
to the app views.

Please note that apps do not have to take over the page where the app itself is
attached. If the app does not have a URLconf entry for ``r'^$'`` the standard
page rendering still happens. because of the recommended catch-all
URLconf entry for pages at the end.
