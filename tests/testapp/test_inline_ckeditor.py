import pytest

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
