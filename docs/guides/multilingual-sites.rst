Multilingual sites
==================

Pages may come in varying languages. ``LanguageMixin`` helps with that.
It uses ``settings.LANGUAGES`` for the language selection, and sets the
first language as default:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from feincms3.mixins import LanguageMixin
    from feincms3.pages import AbstractPage

    class Page(LanguageMixin, AbstractPage):
        pass

The language itself is saved as ``language_code`` on the model. Also
provided is a method ``activate_language`` which activates the selected
language using ``django.utils.translation.activate`` and sets
``LANGUAGE_CODE`` on the request, the same things Django's
``LocaleMiddleware`` does:

.. code-block:: python

    def page_detail(request, path):
        page = ...  # MAGIC! (or maybe get_object_or_404...)
        page.activate_language(request)

.. note::
   ``page.activate_language`` does not persist the language across
   requests as Django's ``django.views.i18n.set_language`` does.
   (``set_language`` modifies the session and sets cookies.) That is
   mostly what you want though since the page's language is tied to its
   URL.


Page tree tips
~~~~~~~~~~~~~~

I most often add a root page per language, which means that the main
navigation's ``tree_depth`` would be ``1``, not ``0``. The menu template
tags described in :ref:`navigation` would also require an additional
``.filter(language_code=django.utils.translation.get_language())``
statement to only return pages in the current language.
