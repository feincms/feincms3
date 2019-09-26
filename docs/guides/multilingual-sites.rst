Multilingual sites
==================

Making the page language selectable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pages may come in varying languages. ``LanguageMixin`` helps with that.
It adds a ``language_code`` field to the model which allows selecting
the language based on ``settings.LANGUAGES``. The first language is set
as default:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from feincms3.mixins import LanguageMixin
    from feincms3.pages import AbstractPage

    class Page(LanguageMixin, AbstractPage):
        pass


Activating the language
~~~~~~~~~~~~~~~~~~~~~~~

The ``activate_language`` method is the preferred way to activate the
page's language for the current request. It runs
``django.utils.translation.activate`` and sets ``request.LANGUAGE_CODE``
to the value of ``django.utils.translation.get_language``, the same
things Django's ``LocaleMiddleware`` does.

Note that ``activate`` may fail and ``get_language`` might return a
different language, however that's not specific to feincms3.

.. code-block:: python

    def page_detail(request, path):
        page = ...  # MAGIC! (or maybe get_object_or_404...)
        page.activate_language(request)
        ...

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

A page tree might look as follows then::

    Home (EN)
    - About us
    - News

    Startseite (DE)
    - Über uns
    - Neuigkeiten

    Page d'acceuil (FR)
    - A propos de nous
    - Actualité
