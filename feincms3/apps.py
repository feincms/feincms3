import warnings

import django


if django.VERSION < (3, 2):
    from feincms3.applications import *  # noqa

    warnings.warn(
        "Django 3.2 will start autodiscovering app configs inside '.apps' modules."
        " We cannot continue using feincms3.apps because the AppsMixin inside this"
        " module can only be loaded after Django initializes all apps."
        " Please change feincms3.apps to feincms3.applications in your code."
        " This compatibility shim will be removed at some point in the future."
        " Sorry for the inconvenience.",
        DeprecationWarning,
        stacklevel=2,
    )
