========
feincms3
========

.. image:: https://travis-ci.org/matthiask/feincms3.svg?branch=master
    :target: https://travis-ci.org/matthiask/feincms3

.. image:: http://readthedocs.org/projects/feincms3/badge/?version=latest
    :target: http://feincms3.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


feincms3 provides additional building blocks on top of
django-content-editor_ and django-cte-forest_ which make building a page
CMS (and also other types of CMS) simpler.

Consult the documentation_ or the example project feincms3-example_ for
additional details.


Coding style
============

feincms3 uses both flake8 and isort to check for style violations. It is
recommended to add the following git hook as an executable file at
``git/hooks/pre-commit``::

    #!/bin/bash
    set -ex
    export PYTHONWARNINGS=ignore
    flake8 .
    isort --recursive --check-only --diff


.. _django-content-editor: http://django-content-editor.readthedocs.org/
.. _django-cte-forest: https://github.com/matthiask/django-cte-forest
.. _feincms3-example: https://github.com/matthiask/feincms3-example
.. _documentation: http://feincms3.readthedocs.io/en/latest/
