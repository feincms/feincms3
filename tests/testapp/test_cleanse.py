from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps

from feincms3.cleanse import CleansedRichTextField


class Test(TestCase):
    @isolate_apps("testapp")
    def test_mixin(self):
        class Thing(models.Model):  # noqa: DJ008
            text = CleansedRichTextField()

        thing = Thing(text="<script>Hello</script>World")
        thing.full_clean()
        self.assertEqual(thing.text, "World")
