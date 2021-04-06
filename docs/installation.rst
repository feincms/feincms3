Prerequisites and installation
==============================

feincms3 runs on Python 3.6 or better. The minimum
required Django version is 2.2. Database engine support is constrained
by `django-tree-queries
<https://github.com/matthiask/django-tree-queries>`_ use of recursive
common table expressions. At the time of writing, this means that
PostgreSQL, sqlite3 (>3.8.3) and MariaDB (>10.2.2) are supported. MySQL
8.0 should work as well, but is not being tested.

The best way to install feincms3 is:

.. code-block:: shell

    pip install 'feincms3[all]'  # Quote the requirement to escape globbing

This installs all optional dependencies as required by the bundled rich
text, image and oEmbed plugins. Should you be using Z-shell (zsh), then use ``pip install 'feincms3[all]'`` to escape globbing. A more minimal installation can be
selected by only running ``pip install feincms3``
