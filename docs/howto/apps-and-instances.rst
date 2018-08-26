Apps and instances
==================

Applications can be added to the tree several times. Django itself
supports this through the differentiation between `application
namespaces and instance namespaces
<https://docs.djangoproject.com/en/2.1/topics/http/urls/#url-namespaces-and-included-urlconfs>`__.
feincms3 builds on this functionality.


``reverse`` vs ``reverse_app``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reverse`` may not find apps because Django is content with the first
match when searching for matching namespaces. Also, ``reverse`` may not
find the best match in the presence of several app instances, be it
because of several languages on the site or because of other factors.


Reversing URLs outside the request-response cycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

... describe :func:`feincms3.apps.apps_urlconf`

Use this:

.. code-block:: python

   from django.urls import reverse
   from feincms3.apps import apps_urlconf

   reverse("apps:blog:article-list", urlconf=apps_urlconf())

Or maybe better yet:

.. code-block:: python

    from feincms3.apps import apps_urlconf, reverse_app

    reverse_app("blog", "article-list", urlconf=apps_urlconf())
