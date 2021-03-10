import warnings

import django


if django.VERSION < (3, 2):
    from feincms3.applications import *  # noqa

    warnings.warn(
        "Django 3.2 will start autodiscovering app configs inside '.apps' modules,"
        " which causes trouble for our model mixins."
        " Please change feincms3.apps to feincms3.applications in your code."
        " This compatibility shim will be removed at some point in the future."
        " Sorry for the inconvenience.",
        DeprecationWarning,
        stacklevel=2,
    )
