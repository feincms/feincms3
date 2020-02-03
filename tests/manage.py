#!/usr/bin/env python
import os
import sys
from os.path import abspath, dirname


# Patch some stuff for Django 3.1 (because versatileimagefield isn't compatible yet)
try:
    from django.utils import six  # noqa
except ImportError:
    import six

    sys.modules["django.utils.six"] = six

try:
    from django.utils.encoding import python_2_unicode_compatible  # noqa
except ImportError:
    from django.utils import encoding

    encoding.python_2_unicode_compatible = lambda x: x

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")

    sys.path.insert(0, dirname(dirname(abspath(__file__))))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
