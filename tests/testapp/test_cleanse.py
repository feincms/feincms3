from django.db import models
from django.test.utils import isolate_apps

from feincms3.cleanse import CleansedRichTextField


@isolate_apps("testapp")
def test_mixin():
    class Thing(models.Model):  # noqa: DJ008
        text = CleansedRichTextField()

    thing = Thing(text="<script>Hello</script>World")
    thing.full_clean()
    assert thing.text == "World"
