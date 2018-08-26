Multilingual sites
==================

``LanguageMixin``, ``page.activate_language(request)``, ...


Page tree tips
~~~~~~~~~~~~~~

I most often add a root page per language, which means that the main
navigation ``tree_depth`` would be ``1``, not ``0``. The menu template
tags would require an additional
``.filter(language_code=django.utils.translation.get_language())``
statement to only return pages in the current language.
