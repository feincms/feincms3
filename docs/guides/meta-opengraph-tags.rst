Meta and OpenGraph tags
=======================

`feincms3-meta
<https://github.com/matthiask/feincms3-meta>`__'s documentation:

Helpers and mixins for making meta and `open graph <http://ogp.me>`__
tags less annoying.

``pip install feincms3-meta``

Inherit ``feincms3_meta.models.MetaMixin``

Optional, but recommended: Add a setting for default tags:

.. code-block:: python

    META_TAGS = {
        "site_name": "My site",
        "title": "Default title",
        "description": (
            "The default description,"
            " maybe long."
        ),
        "image": "/static/app/logo.png",
    }

If you define ``fieldsets`` on a ``ModelAdmin`` subclass, you may
want to use the helper ``MetaMixin.admin_fieldset()``, or maybe not.

Use the dictionary returned by ``feincms3_meta.utils.meta_tags``
either directly (its ``__str__`` method renders as a HTML fragment)
or access individual properties using standard dictionary access:

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

The rendering of a meta tags dictionary is also usable standalone
with ``feincms3_meta.utils.format_meta_tags``.
