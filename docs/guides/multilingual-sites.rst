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

By manually setting the slug of all root pages to their respective
language code you can generate a navigation pointing to all sites in
their respective language (assuming that the built-in template context
processor ``django.template.context_processors.i18n`` is active):

.. code-block:: html+django

    <nav class="languages">
    {% for code, name in LANGUAGES %}
      <a href="/{{ code }}/">{{ name }}</a>
    {% endfor %}
    </nav>


Deep links to pages in other languages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The navigation snippet above does not link translations directly but
instead always shows the home page to visitors. It may be preferrable to
define pages (and other CMS objects) as translations of each other so
that it is possible to generate a navigation menu directly linking the
same content in different languages directly.

feincms3 offers a built-in way to achieve this. Instead of inheriting
the default :class:`feincms3.mixins.LanguageMixin` inherit the
:class:`feincms3.mixins.LanguageAndTranslationOfMixin`. The latter
provides an additional ``translation_of`` foreign key which allows
linking pages in other languages to the page in the first language in
the ``LANGUAGES`` setting's list. In the example above, you could
specify that "Über uns" is the german translation of "About us", and "A
propos de nous" the french translation of "About us". The
:func:`feincms3.mixins.LanguageAndTranslationOfMixin.translations`
method returns a list of all known translations. Together with the
:func:`~feincms3.templatetags.feincms3.translations` template filter you
can generate a navigation menu as follows (assuming that ``object`` is
the current page):

.. code-block:: html+django

    {% load feincms %}
    <nav class="languages">
    {% for lang in page.translations.active|translations %}
      <a href="{% if lang.object %}{{ lang.object.get_absolute_url }}{% else %}/{{ lang.code }}/{% endif %}">
        {{ lang.name }}
      </a>
    {% endfor %}
    </nav>


.. note::
   The same should work for any CMS object inheriting
   :class:`feincms3.mixins.LanguageAndTranslationOfMixin`, and should also
   work when used within a feincms3 :ref:`app <apps-introduction>`.

   In this case it may be extra-important to wrap the object's call to
   ``reverse_app`` in a block which overrides the active language:

   .. code-block:: python

       from django.utils.translation import override
       from feincms3.apps import reverse_app

       class Article(LanguageAndTranslationOfMixin, ...):
           def get_absolute_url(self):
               with override(self.language_code):
                   return reverse_app("articles", "detail", ...)
