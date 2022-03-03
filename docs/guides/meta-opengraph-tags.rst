Meta and OpenGraph tags
=======================

The recommended way to add meta and `open graph <http://ogp.me>`__ tags
information to pages and other CMS objects is using `feincms3-meta
<https://github.com/matthiask/feincms3-meta>`__.

Installation and configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the package:

.. code-block:: shell

    pip install feincms3-meta

Make the page model inherit the mixin:

.. code-block:: python

    from feincms3.pages import AbstractPage
    from feincms3_meta.models import MetaMixin

    class Page(AbstractPage, MetaMixin, ...):
        pass

If you define ``fieldsets`` on a ``ModelAdmin`` subclass, you may
want to use the helper ``MetaMixin.admin_fieldset()``, or maybe not.

Add settings (optional, but recommended):

.. code-block:: python

    META_TAGS = {
        "site_name": "My site",
        "title": "Default title",
        "description": (
            "The default description,"
            " maybe long."
        ),
        "image": "/static/app/logo.png",
        # "author": "...",
        "robots": "index,follow,noodp",
    }

    # Only for translations
    INSTALLED_APPS.append("feincms3_meta")


Rendering
~~~~~~~~~

The dictionary subclass returned by ``feincms3_meta.utils.meta_tags``
can either be used as a dictionary, or rendered directly (its
``__str__`` method returns a HTML fragment):

.. code-block:: python

    from feincms3_meta.utils import meta_tags

    # ...
    return render(
        request,
        ...,
        {
            "page": page,
            "page_regions": ...,
            ...
            "meta_tags": meta_tags([page], request=request),
        },
    )

``meta_tags`` also supports overriding or removing individual tags
using keyword arguments. Falsy values are discarded, ``None`` causes
the complete removal of the tag from the dictionary.

If you want to inherit meta tags from ancestors (or from other objects)
provide more than one object to the ``meta_tags`` function:

.. code-block:: python

    ancestors = list(page.ancestors())
    tags = meta_tags(request=request).add(*ancestors).add(page)

Since you may also need the ancestors when using regions which inherit content
from the page's ancestors when they are empty it is recommended to put the meta
tags generation into the ``page_context`` function described in
:ref:`build-your-cms`. Note that ``inherit_from`` wants a reversed list of
ancestors (from bottom to top) but ``meta_tags`` wants ancestors from top to
bottom so that more specific values from lower in the page tree override their
ancestors values:

.. code-block:: python

    def page_context(request, *, page):
        # page = page or page_for_app_request(request)
        page.activate_language(request)
        ancestors = list(page.ancestors())
        return {
            "page": page,
            "page_regions": renderer.regions_from_item(
                page,
                inherit_from=reversed(ancestors),
                timeout=30,
            ),
            "meta_tags": meta_tags(request=request).add(*ancestors).add(page),
        }

.. note::
   If you want to further override meta tags e.g. in an application (see
   :ref:`apps-introduction`) you may want to run the above function and reach
   into the context:

   .. code-block:: python

    page = page_for_app_request(request)
    context = page_context(request, page=page)

    # Example: Article detail page
    article = get_object_or_404(Article, ...)
    context["meta_tags"].add(article)

    return render(...)
