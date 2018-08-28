.. _apps-and-instances:

Apps and instances
==================

.. note::
   This guide builds on :ref:`apps-form-builder`.

Applications can be added to the tree several times. Django itself
supports this through the differentiation between `application
namespaces and instance namespaces
<https://docs.djangoproject.com/en/2.1/topics/http/urls/#url-namespaces-and-included-urlconfs>`__.
feincms3 builds on this functionality.

The :func:`feincms3.apps.apps_urlconf` function generates a dynamic
URLconf Python module including all applications in their assigned place
and adding the ``urlpatterns`` from ``ROOT_URLCONF`` at the end (or
returns the value of ``ROOT_URLCONF`` directly if there are no active
applications).


Application namespaces and instance namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The application URLconfs are included using nested namespaces:

- The outer application namespace is ``"apps"`` by default.
- The outer instance namespace is ``"apps-" + LANGUAGE_CODE``.
- The inner namespace is the app namespace, specified by the value of
  ``app_name`` în the apps' URLconf module. The string must correspond
  with the value used in the ``APPLICATIONS`` list on the page model.
  application's name in the ``APPLICATIONS`` list.
- The inner instance namespace is the same as the app namespace, except
  if you return a different value in the applications
  ``app_instance_namespace`` function specified in the ``APPLICATIONS``
  list.

Apps are contained in nested URLconf namespaces which
allows for URL reversing using Django's ``reverse()`` mechanism. The
inner namespace is the app itself, the outer namespace the language.
(Currently the apps code depends on
:class:`~feincms3.mixins.LanguageMixin` and cannot be used without it.)
:func:`~feincms3.apps.reverse_app` hides a good part of the complexity
of finding the best match for a given view name since apps will often be
added several times in different parts of the tree, especially on sites
with more than one language.


Reversing application URLs
~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way for reversing app URLs is by using
:func:`feincms3.apps.reverse_app`. The method expects at least two
arguments, a namespace and a viewname. The namespace argument also
supports passing a list of namespaces which is useful in conjunction
with the ``app_instance_namespace`` option of applications.

:func:`~feincms3.apps.reverse_app` first generates a list of viewnames
and passes them on to :func:`feincms3.apps.reverse_any` (which returns
the first viewname that can be reversed to a URL).

For the sake of an example let's assume that our site is configured with
english, german and french as available languages and that we're trying
to reverse the article list page, and that we are processing a german
page:

.. code-block:: python

    from feincms3.apps import reverse_app

    def page_detail(request, path=None):
        page = ...
        page.activate_language(request)

        articles_list_url = reverse_app("articles", "article-list")
        ...

The list of viewnames reversed is in order:

- ``apps-de.articles.article-list``
- ``apps-en.articles.article-list``
- ``apps-fr.articles.article-list``

The german apps namespace comes first in the list. If the german part of
the site does not contain an articles app, the reversing continues in
all other languages.

If the namespace argument to :func:`~feincms3.apps.reverse_app` was a
list (or tuple), the list is even longer. Suppose that variants of the
articles app may be added to the tree where only a single category is
shown:

.. code-block:: python

    class Page(AppsMixin, LanguageMixin, ..., AbstractPage):
        APPLICATIONS = [
            ("articles", _("Articles"), {
                "urlconf": "app.articles.urls",
                "app_instance_namespace": lambda page: "{}-{}".format(
                    page.application, page.category_id or "all"
                ),
            }),
            ...
        ]

        category = models.ForeignKey(
            "articles.Category",
            blank=True,
            null=True,
            ...
        )

In this case we might prefer the URL of a specific categories' articles
app, but also be content with an articles app without a specific
category:

.. code-block:: python

    reverse_app(
        ["articles-{}".format(category.pk), "articles"],
        "article-list"
    )

The list of viewnames in this case is (assuming that the category has a
``pk`` value of 42):

- ``apps-de.articles-42.article-list``
- ``apps-de.articles.article-list``
- ``apps-en.articles-42.article-list``
- ``apps-en.articles.article-list``
- ``apps-fr.articles-42.article-list``
- ``apps-fr.articles.article-list``

As you can see ``reverse_app`` prefers apps in the current language to
apps with the closer matching instance namespace.

.. note::
   Some of the time Django's stock ``reverse()`` function works as well
   for reversing app URLs, e.g:

   .. code-block:: python

       from django.urls import reverse

       reverse("apps:articles:article-list")

   However, it's still recommended to use ``reverse_app``. ``reverse``
   may not find apps because Django is content with the first match when
   searching for matching namespaces. Also, ``reverse`` may not find the
   best match in the presence of several app instances, be it because of
   several languages on the site or because of other factors.


Reversing URLs outside the request-response cycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Outside the request-response cycle, respectively outside
:func:`feincms3.apps.apps_middleware`'s ``request.urlconf`` assignment,
the reversing functions only use the URLconf module configured using the
``ROOT_URLCONF`` setting. In this case applications are impossible to
find. However, all reversing functions support specifying the root URLconf
module used for reversing:

.. code-block:: python

    from feincms3.apps import apps_urlconf, reverse_app

    reverse_app("articles", "article-list", urlconf=apps_urlconf())
