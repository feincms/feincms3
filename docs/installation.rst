Prerequisites and installation
==============================

feincms3 runs on Python 2.7 and Python 3.4 or better. The minimum
required Django version is 1.11. Database engine support is constrained
by `django-tree-queries
<https://github.com/matthiask/django-tree-queries>`_ use of recursive common table expressions. At
the time of writing, this means that PostgreSQL, sqlite3 (>3.8.3) and
MariaDB (>10.2.2) are supported. MySQL 8.0 should work as well, but is
not being tested.

feincms3 should be installed using `pip <https://pip.pypa.io>`_. The
default of ``pip install feincms3`` depends on `django-content-editor
<https://django-content-editor.readthedocs.io>`_ and
`django-tree-queries
<https://github.com/matthiask/django-tree-queries>`_
(explained below). By specifying ``pip install feincms3[all]`` instead
you can also install all optional dependencies (otherwise you'll not be
able to use the built-in rich text, image and oEmbed plugins).

.. note::
   This documentation uses Python 3's keyword-only syntax in a few
   places. Python 2 does not support keyword-only arguments, but keyword
   usage is still enforced in feincms3.
