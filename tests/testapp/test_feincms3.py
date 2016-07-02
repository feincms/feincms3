import re
import time

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone
from django.utils.http import urlunquote

# from email_registration.utils import get_signer, send_registration_mail


def _messages(response):
    return [m.message for m in response.context['messages']]


class TestTest(TestCase):
    def test_setup(self):
        pass
