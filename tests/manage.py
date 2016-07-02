#!/usr/bin/env python
from os.path import abspath, dirname
import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")

    sys.path.insert(0, dirname(dirname(abspath(__file__))))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
