import warnings

import pytest
from django.db import models
from django.test.utils import isolate_apps

from feincms3.inline_ckeditor import CKEDITOR_CONFIG, InlineCKEditorField


CKEDITOR_CONFIG["test"] = "test"


def test_config():
    """Various ways of configuring the InlineCKEditorField"""

    field = InlineCKEditorField(config_name="test")
    assert field.widget_config == {"ckeditor": None, "config": "test"}

    field = InlineCKEditorField(config="test2")
    assert field.widget_config == {"ckeditor": None, "config": "test2"}

    field = InlineCKEditorField(ckeditor="test")
    assert field.widget_config == {"ckeditor": "test", "config": None}

    with pytest.raises(KeyError):
        InlineCKEditorField(config_name="_does_not_exist")

    with pytest.raises(TypeError):
        InlineCKEditorField(config_name="test", config="test2")


@isolate_apps("testapp")
def test_deprecation():
    """Concrete models using the InlineCKEditorField emit a deprecation warning"""

    class Abstract(models.Model):
        text = InlineCKEditorField()

        class Meta:
            abstract = True

    with warnings.catch_warnings():
        warnings.simplefilter("error")

        class Overridden(Abstract):  # noqa: DJ008
            text = models.TextField()

    with pytest.warns(DeprecationWarning, match=r"testapp\.Concrete\.text"):

        class Concrete(Abstract):  # noqa: DJ008
            pass

    [warning] = Concrete._meta.get_field("text").check()
    assert warning.id == "feincms3.W007"
    assert "django-prose-editor" in warning.hint
