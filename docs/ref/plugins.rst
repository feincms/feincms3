Plugins (``feincms3.plugins``)
==============================

All documented plugin classes and functions can be imported from
``feincms3.plugins`` as well.

.. note::
   The content types in `FeinCMS <https://github.com/feincms/feincms>`__
   had ways to process requests and responses themselves, the
   ``.process()`` and ``.finalize()`` methods. feincms3 plugins do not
   offer this. The feincms3 way to achieve the same thing is by using
   :ref:`apps <apps-and-instances>` or by adding the functionality in
   your own views (which are much simpler than the view in FeinCMS was).


External
~~~~~~~~

.. automodule:: feincms3.plugins.external
   :members:


HTML
~~~~

.. automodule:: feincms3.plugins.html
   :members:


Images
~~~~~~

.. automodule:: feincms3.plugins.image
   :members:


Rich text
~~~~~~~~~

.. automodule:: feincms3.plugins.richtext
   :members:


Snippets
~~~~~~~~

.. automodule:: feincms3.plugins.snippet
   :members:


Versatile images
~~~~~~~~~~~~~~~~

.. automodule:: feincms3.plugins.versatileimage
   :members:
