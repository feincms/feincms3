.. _contributing:

Contributing
============

This isn't a `Jazzband <https://jazzband.co>`__ project, but by
contributing you agree to abide to the same `Contributor Code of Conduct
<https://jazzband.co/about/conduct>`__ as if it was one.


Bug reports and feature requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can report bugs and request features in the `bug tracker
<https://github.com/matthiask/feincms3/issues>`__.


Code
~~~~

The code is available `on GitHub
<https://github.com/matthiask/feincms3>`__.

To work on the code I strongly recommend installing `tox
<https://tox.readthedocs.io>`__. I use tox as a glorified
virtualenv-builder and task runner for local development.

Available tasks are:

* ``tox -e style``: Reformats the code using black and runs flake8.
* ``tox -e docs``: Builds the HTML docs into ``build/docs/html/``
* ``tox -e py??-dj?'``: Runs tests using combinations of Python and
  Django. See ``tox -l`` for all available combinations.

Both testing tasks also generate HTML-based code coverage output into
the ``htmlcov/`` folder.


Style
~~~~~

Python code for the feincms3 project may be automatically formatted and
checked using ``tox -e style``. The coding style is also checked when
building pull requests using Github actions.


Patches and translations
~~~~~~~~~~~~~~~~~~~~~~~~

Please submit `pull requests
<https://github.com/matthiask/feincms3/pulls>`__!

I am not using a centralized tool for translations right now, I'll
happily accept them as a patch too.


Mailing list
~~~~~~~~~~~~

If you wish to discuss a topic, please open an issue on Github.
Alternatively, the `django-feincms
<https://groups.google.com/forum/#!forum/django-feincms>`__ Google Group
may also be used for discussing this project.
