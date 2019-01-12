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

    class Page(MetaMixin, ..., AbstractPage):
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

    def page_detail(request, path=None):
        page = ...
        return render(request, ..., {
            "page": page,
            "regions": ...,
            ...
            "meta_tags": meta_tags([page], request=request),
        })

``meta_tags`` also supports overriding or removing individual tags
using keyword arguments. Falsy values are discarded, ``None`` causes
the complete removal of the tag from the dictionary.

If you want to inherit meta tags from ancestors (or from other objects)
provide more than one object to the ``meta_tags`` function:

.. code-block:: python

    ancestors = list(page.ancestors().reverse())
    tags = meta_tags([page] + ancestors, request=request)
