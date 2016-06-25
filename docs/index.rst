===========================================
feincms3 -- Tools for building your own CMS
===========================================

.. image:: https://travis-ci.org/matthiask/feincms3.svg?branch=master
    :target: https://travis-ci.org/matthiask/feincms3

.. warning::

   Experimentally experimental experiment.


feincms3 provides additional building blocks on top of
django-content-editor_ and django-mptt_ which make building a page CMS
(and also other types of CMS) simpler. This guide shows how a simple
multilingual page CMS including a articles app may be built, and shows how
feincms3 helps in this undertaking.


.. toctree::
   :maxdepth: 2

   models

   apps
   cleanse
   mixins
   plugins
   shortcuts
   templatetags


.. _django-content-editor: http://django-content-editor.readthedocs.org/
.. _django-mptt: http://django-mptt.github.io/django-mptt/
