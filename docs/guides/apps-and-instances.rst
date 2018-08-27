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


``reverse`` vs ``reverse_app``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reverse`` may not find apps because Django is content with the first
match when searching for matching namespaces. Also, ``reverse`` may not
find the best match in the presence of several app instances, be it
because of several languages on the site or because of other factors.


Reversing URLs outside the request-response cycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this:

.. code-block:: python

   from django.urls import reverse
   from feincms3.apps import apps_urlconf

   reverse("apps:blog:article-list", urlconf=apps_urlconf())

Or maybe better yet:

.. code-block:: python

    from feincms3.apps import apps_urlconf, reverse_app

    reverse_app("blog", "article-list", urlconf=apps_urlconf())
