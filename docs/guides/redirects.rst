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
requests which would result in a 404 response otherwise. A system check
(``feincms3.E008``) reports a missing middleware:

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
moved. The query string of the request is kept. Errors raised by
``get_absolute_url()`` while recording are logged and do not prevent saving
the object.

The ``queryset`` determines which objects may be redirected to, e.g. only
active pages. It may also be a callable accepting the request. Old URLs of
inactive or deleted objects result in a 404 response.

If ``get_absolute_url()`` uses related objects, pass them as
``select_related``, so that looking up redirects and listing them in the
admin doesn't need one query per object:

.. code-block:: python

    # A chapter's URL is built from the URL of its manual's page
    redirects.register(Chapter, select_related=["page"])

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


Why URLs are recorded on every save
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current URL of an object is recorded each time it is saved, even though
most objects never move, instead of recording the old URL only when it
changes. Recording only changes would keep the table small, but would miss
many changes:

- An URL often changes without the object itself being saved. Articles change
  their URL when the page their app is attached to moves; a manual's chapters
  change their URL when the manual's page moves. Only the page is saved in
  this case. Recording the old URLs of all objects whose URLs depend on the
  page would require knowing those dependencies, which ``get_absolute_url()``
  doesn't reveal. When the current URL has been recorded beforehand, the old
  URL is already there and still points to the object.
- Determining the old URL when saving requires the object's old state,
  including the old state of related objects (e.g. the parent page's old
  path). That's an additional query per save and brittle at best.

The price is one upsert query per save of a registered object, and one row per
object (plus one per old URL) in the table. ``record_redirects`` has to be run
once when introducing the app so that existing objects' URLs are known before
they change.


Manual redirects
----------------

Redirects can also be added in the Django admin, e.g. for URLs of an old
website. A redirect either points to an URL or to an object of a registered
model. Redirects to objects follow the object when its URL changes, and are
only used if the object is contained in the queryset of the registration.
Redirects pointing to deleted objects aren't removed automatically, so their
target can be changed to another object later.

The path may contain a query string, e.g. ``/index.php?id=12``. Requests are
matched with their query string first, then without. Editing an automatically
recorded redirect turns it into a manual redirect. Note that when an object
is saved, its current URL is recorded even if a manual redirect for the same
URL exists, since the object is served at the URL anyway.

Redirects can be temporary (status code 302) instead of permanent (status code
301).


Migrating from django-simple-redirects
--------------------------------------

`django-simple-redirects <https://github.com/feinheit/django-simple-redirects>`__
matches the percent-encoded path including the query string and always
responds with temporary redirects. The following data migration copies all
redirects and keeps them temporary. Redirects without a target are skipped
since they only redirected to the empty URL:

.. code-block:: python

    from urllib.parse import unquote

    from django.db import migrations


    def forwards(apps, schema_editor):
        Old = apps.get_model("simple_redirects", "Redirect")
        New = apps.get_model("feincms3_redirects", "Redirect")
        redirects = []
        for old in Old.objects.exclude(new_path=""):
            path, sep, query = old.old_path.partition("?")
            redirects.append(
                New(
                    path=f"{unquote(path)}{sep}{query}",
                    target_url=old.new_path,
                    permanent=False,
                )
            )
        New.objects.bulk_create(redirects, ignore_conflicts=True)


    class Migration(migrations.Migration):
        dependencies = [
            ("feincms3_redirects", "0001_initial"),
            ("simple_redirects", "0001_initial"),
        ]
        operations = [migrations.RunPython(forwards)]

Afterwards, remove ``simple_redirects`` and its middleware from your settings.
Redirects pointing to pages may be changed to point to the page objects in the
admin, so that they keep working when the pages are moved.
