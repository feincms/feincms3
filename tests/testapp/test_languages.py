import pytest
from django.core.exceptions import ValidationError
from django.template import Context, Template

from feincms3.applications import _del_apps_urlconf_cache, apps_urlconf
from feincms3.templatetags.feincms3 import translations, translations_from
from testapp.models import Page, TranslatedArticle
from testapp.utils import override_urlconf


@pytest.mark.django_db
def test_language_and_translation_of_mixin():
    """LanguageAndTranslationOfMixin.translations testing"""
    original = Page.objects.create(
        title="home-en",
        slug="home-en",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )
    translation = Page.objects.create(
        title="home-de",
        slug="home-de",
        path="/de/",
        static_path=True,
        language_code="de",
        is_active=True,
        menu="main",
        translation_of=original,
    )
    translation_fr = Page.objects.create(
        title="home-fr",
        slug="home-fr",
        path="/fr/",
        static_path=True,
        language_code="fr",
        is_active=False,  # Important!
        menu="main",
        translation_of=original,
    )

    assert set(original.translations()) == {original, translation, translation_fr}
    assert set(original.translations().active()) == {original, translation}
    assert set(translation.translations().active()) == {original, translation}

    assert [
        language["object"]
        for language in translations(translation.translations().active())
    ] == [original, translation, None]

    original.delete()
    translation.refresh_from_db()

    assert set(translation.translations()) == set()


@pytest.mark.django_db
def test_language_and_translation_of_mixin_in_app():
    """LanguageAndTranslationOfMixin when used within a feincms3 app"""
    _del_apps_urlconf_cache()

    p = Page.objects.create(
        title="home-en",
        slug="home-en",
        language_code="en",
        is_active=True,
        page_type="translated-articles",
    )
    Page.objects.create(
        title="home-de",
        slug="home-de",
        language_code="de",
        translation_of=p,
        is_active=True,
        page_type="translated-articles",
    )

    original = TranslatedArticle.objects.create(title="News", language_code="en")
    translated = TranslatedArticle.objects.create(
        title="Neues", language_code="de", translation_of=original
    )

    assert str(original) == "News"
    assert str(translated) == "Neues"

    assert [
        language["object"] for language in translations(original.translations())
    ] == [original, translated, None]

    assert apps_urlconf() != "testapp.urls"
    with override_urlconf(apps_urlconf()):
        assert original.get_absolute_url() == f"/home-en/{original.pk}/"
        assert translated.get_absolute_url() == f"/home-de/{translated.pk}/"

    t = translations_from(
        p.translations(),
        original.translations(),
        "hello world",
    )
    assert t == [
        {"code": "en", "name": "English", "object": original},
        {"code": "de", "name": "German", "object": translated},
        {"code": "fr", "name": "French", "object": None},
    ]


@pytest.mark.django_db
def test_language_and_translation_of_mixin_validation():
    """Validation logic of LanguageAndTranslationOfMixin works"""
    original = Page.objects.create(
        title="home-en",
        slug="home-en",
        language_code="en",
    )

    with pytest.raises(ValidationError) as cm:
        Page(
            title="translation",
            slug="translation",
            language_code="en",
            translation_of=original,
        ).full_clean()

    assert cm.value.error_dict["translation_of"][0].message == (
        "Objects in the primary language cannot be the translation of another object."
    )

    original = Page.objects.create(
        title="home-de",
        slug="home-de",
        language_code="de",
    )

    with pytest.raises(ValidationError):
        Page(
            title="translation",
            slug="translation",
            language_code="en",
            translation_of=original,
        ).full_clean()


def test_translations_filter_edge_cases():
    """Exercise edge cases of the |translations filter"""
    assert len(translations(None)) == 3
    assert len(translations({})) == 3

    t = Template(
        "{% load feincms3 %}{% for l in c|translations %}{{ l.code }}{% endfor %}"
    )
    assert t.render(Context({"c": None})) == "endefr"
    assert t.render(Context({"c": []})) == "endefr"
    assert t.render(Context({"c": 1})) == "endefr"
