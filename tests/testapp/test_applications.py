import sys
from types import SimpleNamespace

import django
import pytest
from django.core.checks import Error
from django.core.exceptions import ValidationError
from django.template import Context, Template, TemplateSyntaxError
from django.test.utils import isolate_apps
from django.urls import NoReverseMatch, reverse
from django.utils.translation import deactivate_all, override
from pytest_django.asserts import assertContains, assertRedirects

from feincms3 import applications
from feincms3.applications import (
    ApplicationType,
    PageTypeMixin,
    _del_apps_urlconf_cache,
    apps_urlconf,
    reverse_app,
)
from feincms3.pages import AbstractPage
from testapp.models import Article, Page
from testapp.utils import override_urlconf


@pytest.mark.django_db
def test_apps(client):
    """Article app test (two instance namespaces, two languages)"""
    home_de = Page.objects.create(
        title="home",
        slug="home",
        path="/de/",
        static_path=True,
        language_code="de",
        is_active=True,
        menu="main",
    )
    home_en = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )

    for root in (home_de, home_en):
        for app in ("blog", "publications"):
            Page.objects.create(
                title=app,
                slug=app,
                static_path=False,
                language_code=root.language_code,
                is_active=True,
                page_type=app,
                parent_id=root.pk,
            )

    for i in range(7):
        for category in ("publications", "blog"):
            Article.objects.create(title=f"{category} {i}", category=category)

    assertContains(client.get("/de/blog/all/"), 'class="article"', 7)
    assertContains(client.get("/de/blog/?page=2"), 'class="article"', 2)
    assertContains(
        client.get("/de/blog/?page=42"),
        'class="article"',
        2,  # Last page with instances (2nd)
    )
    assertContains(
        client.get("/de/blog/?page=invalid"),
        'class="article"',
        5,  # First page
    )

    response = client.get("/de/blog/")
    assertContains(response, 'class="article"', 5)

    response = client.get("/en/publications/")
    assertContains(response, 'class="article"', 5)

    with override_urlconf(apps_urlconf()):
        article = Article.objects.order_by("pk").first()
        with override("de"):
            assert article.get_absolute_url() == f"/de/publications/{article.pk}/"

        with override("en"):
            assert article.get_absolute_url() == f"/en/publications/{article.pk}/"

            # The german URL is returned when specifying the ``languages``
            # list explicitly.
            assert (
                reverse_app(
                    (article.category, "articles"),
                    "article-detail",
                    kwargs={"pk": article.pk},
                    languages=["de", "en"],
                )
                == f"/de/publications/{article.pk}/"
            )

            if django.VERSION >= (5, 2):
                # Forwarding query and fragment params to reverse() works
                assert (
                    reverse_app(
                        (article.category, "articles"),
                        "article-detail",
                        kwargs={"pk": article.pk},
                        languages=["de", "en"],
                        query={"a": 3},
                        fragment="world",
                    )
                    == "/de/publications/%s/?a=3#world" % article.pk
                )

    response = client.get(f"/de/publications/{article.pk}/")
    assertContains(response, "<h1>publications 0</h1>", 1)

    # The exact value of course does not matter, just the fact that the
    # value does not change all the time.
    _del_apps_urlconf_cache()
    assert apps_urlconf() == "urlconf_fe9552a8363ece1f7fcf4970bf575a47"

    updated = Page.objects.filter(page_type="blog").update(
        page_type="invalid", app_namespace="invalid"
    )
    assert updated == 2

    _del_apps_urlconf_cache()
    assert apps_urlconf() == "urlconf_4bacbaf40cbe7e198373fd8d629e819c"

    # Blog and publications
    assert (
        len(
            sys.modules["urlconf_fe9552a8363ece1f7fcf4970bf575a47"]
            .urlpatterns[0]
            .url_patterns
        )
        == 2
    )
    # Only publications, invalid apps are filtered out
    assert (
        len(
            sys.modules["urlconf_4bacbaf40cbe7e198373fd8d629e819c"]
            .urlpatterns[0]
            .url_patterns
        )
        == 1
    )


@pytest.fixture
def apps_validation_models():
    home = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )
    blog = Page.objects.create(
        title="blog",
        slug="blog",
        language_code="en",
        is_active=True,
        menu="main",
        page_type="blog",
        parent=home,
    )
    return home, blog


@pytest.mark.django_db
def test_apps_duplicate(apps_validation_models):
    """Test that apps cannot be added twice with the exact same configuration"""
    deactivate_all()

    home, blog = apps_validation_models

    home2 = Page.objects.create(
        title="home",
        slug="home",
        path="/en2/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )
    blog2 = Page.objects.create(
        title="blog",
        slug="blog",
        language_code="en",
        is_active=True,
        menu="main",
        page_type="blog",
        parent=home2,
    )

    with pytest.raises(ValidationError) as cm:
        blog2.full_clean()

    assert cm.value.error_dict["page_type"][0].message == (
        'The page type "blog" with the specified configuration exists already.'
    )


@pytest.mark.django_db
def test_apps_required_fields():
    """Apps can have required fields"""
    deactivate_all()

    home = Page(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
        page_type="importable_module",
    )
    with pytest.raises(ValidationError) as cm:
        home.full_clean(exclude=["not_editable"])

    assert cm.value.error_dict["optional"][0].message == (
        'This field is required for the page type "importable_module".'
    )

    home.optional = 1
    home.not_editable = 2
    home.full_clean(exclude=["not_editable"])


@pytest.mark.django_db
def test_apps_cloning_validation(admin_client, apps_validation_models):
    """Checks that the target is properly validated when cloning"""
    deactivate_all()

    home, blog = apps_validation_models

    clone_url = reverse("admin:testapp_page_clone", args=(blog.pk,))

    response = admin_client.get(clone_url)
    assertContains(response, "_set_content")
    assertContains(response, "set_page_type")

    response = admin_client.post(clone_url, {"target": home.pk, "set_page_type": True})
    assertContains(
        response,
        "The page type &quot;blog&quot; with the specified configuration exists already.",
    )

    # The other way round works
    clone_url = reverse("admin:testapp_page_clone", args=(home.pk,))

    response = admin_client.post(clone_url, {"target": blog.pk, "set_page_type": True})
    assertRedirects(response, reverse("admin:testapp_page_change", args=(blog.pk,)))

    # No apps in tree anymore
    assert Page.objects.filter(page_type="blog").count() == 0


@pytest.mark.django_db
def test_reverse_app_tag():
    """Exercise the {% reverse_app %} template tag"""
    Page.objects.create(
        title="blog",
        slug="blog",
        static_path=False,
        language_code="en",
        is_active=True,
        page_type="blog",
    )

    tests = [
        ("{% reverse_app 'blog' 'article-detail' pk=42 %}", "/blog/42/", {}),
        (
            "{% reverse_app 'blog' 'article-detail' pk=42 fallback='/a/' %}",
            "/blog/42/",
            {},
        ),
        (
            "{% reverse_app namespaces 'article-detail' pk=42 fallback='/a/' as a %}{{ a }}",
            "/blog/42/",
            {"namespaces": ["stuff", "blog"]},
        ),
        ("{% reverse_app 'bla' 'bla' fallback='/test/' %}", "/test/", {}),
        (
            "{% reverse_app 'bla' 'bla' fallback='/test/' as t %}{{ t }}",
            "/test/",
            {},
        ),
        ("{% reverse_app 'bla' 'bla' as t %}{{ t|default:'blub' }}", "blub", {}),
    ]

    with override_urlconf(apps_urlconf()):
        for tpl, out, ctx in tests:
            t = Template("{% load feincms3 %}" + tpl)
            assert t.render(Context(ctx)).strip() == out

        with pytest.raises(NoReverseMatch):
            Template("{% load feincms3 %}{% reverse_app 'a' 'a' 42 %}").render(
                Context()
            )


def test_reverse_app_failures():
    """Invalid parameters to {% reverse_app %}"""
    with pytest.raises(TemplateSyntaxError) as cm:
        Template("{% load feincms3 %}{% reverse_app %}")
    assert str(cm.value) == (
        "'reverse_app' takes at least two arguments, a namespace and a URL pattern name."
    )


def test_apps_urlconf_no_apps():
    """apps_urlconf returns the ROOT_URLCONF when there are no apps at all"""
    assert apps_urlconf(apps=[]) == "testapp.urls"


def test_application_type():
    """Overriding ``app_namespace`` should be possible"""

    with pytest.raises(TypeError):
        ApplicationType()

    at = ApplicationType(
        key="test",
        title="test",
        urlconf="test",
        app_namespace=lambda page: f"{page.page_type}-{page.category_id}",
    )

    assert (
        at.app_namespace(SimpleNamespace(page_type="blog", category_id=3)) == "blog-3"
    )

    at = ApplicationType(
        key="test",
        title="test",
        urlconf="test",
    )
    assert at.app_namespace(SimpleNamespace(page_type="blog", category_id=3)) == "blog"


@isolate_apps("testapp")
def test_importable_page_types():
    """Applications require an importable URLconf module"""

    apps_model = applications._APPS_MODEL
    try:

        class Page(AbstractPage, PageTypeMixin):
            TYPES = [ApplicationType(key="app", title="app", urlconf="does-not-exist")]

        errors = Page.check()
        expected = [
            Error(
                "The application type 'app' has an unimportable"
                " URLconf value 'does-not-exist': No module named 'does-not-exist'",
                obj=Page,
                id="feincms3.E003",
            ),
        ]
        assert errors == expected

    finally:
        applications._APPS_MODEL = apps_model


@isolate_apps("testapp")
def test_unique_page_types():
    """Page types must have unique keys"""

    apps_model = applications._APPS_MODEL
    try:

        class Page(AbstractPage, PageTypeMixin):
            TYPES = [
                ApplicationType(key="app", title="a", urlconf="importable_module"),
                ApplicationType(key="app", title="a", urlconf="importable_module"),
            ]

        errors = Page.check()
        expected = [
            Error(
                "Page type keys are used more than once: app.",
                obj=Page,
                id="feincms3.E006",
            ),
        ]
        assert errors == expected

    finally:
        applications._APPS_MODEL = apps_model
