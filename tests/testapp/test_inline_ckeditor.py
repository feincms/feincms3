from django.test import TestCase

from feincms3.inline_ckeditor import CKEDITOR_CONFIG, InlineCKEditorField


CKEDITOR_CONFIG["test"] = "test"


class Test(TestCase):
    def test_config(self):
        """Various ways of configuring the InlineCKEditorField"""

        field = InlineCKEditorField(config_name="test")
        self.assertEqual(field.widget_config, {"ckeditor": None, "config": "test"})

        field = InlineCKEditorField(config="test2")
        self.assertEqual(field.widget_config, {"ckeditor": None, "config": "test2"})

        field = InlineCKEditorField(ckeditor="test")
        self.assertEqual(field.widget_config, {"ckeditor": "test", "config": None})

        with self.assertRaises(KeyError):
            InlineCKEditorField(config_name="_does_not_exist")

        with self.assertRaises(TypeError):
            InlineCKEditorField(config_name="test", config="test2")
