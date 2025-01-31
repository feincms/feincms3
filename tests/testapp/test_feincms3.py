import re

import pytest
from django.contrib.auth.models import User
from django.core.checks import Warning
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.template import Context, Template
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext, isolate_apps, override_settings
from django.urls import NoReverseMatch, reverse
from pytest_django.asserts import assertContains, assertRedirects

from feincms3 import mixins
from feincms3.applications import (
    reverse_any,
    reverse_app,
    reverse_fallback,
)
from feincms3.pages import AbstractPage
from feincms3.regions import Regions
from feincms3.renderer import TemplatePluginRenderer
from feincms3.shortcuts import render_list
from testapp.models import HTML, Article, Page


def zero_management_form_data(prefix):
    return {
        f"{prefix}-TOTAL_FORMS": 0,
        f"{prefix}-INITIAL_FORMS": 0,
    }


def merge_dicts(*dicts):
    res = {}
    for d in dicts:
        res.update(d)
    return res


@pytest.fixture
def user():
    return User.objects.create_superuser("admin", "admin@test.ch", "blabla")


@pytest.fixture
def client(client, user):
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_modules(client):
    """Admin modules are present, necessary JS too"""
    response = client.get("/admin/")
    assertContains(response, '<a href="/admin/testapp/page/">Pages</a>', 1)

    response = client.get("/admin/testapp/page/")
    assertContains(response, "/static/feincms3/admin.css", 1)
    assert "/static/content_editor/content_editor.js" not in response.content.decode()

    response = client.get("/admin/testapp/page/add/")
    assertContains(response, "/static/content_editor/content_editor.js", 1)


@pytest.mark.django_db
def test_add_empty_page(client):
    """Add a page without content, test path generation etc"""
    response = client.post(
        "/admin/testapp/page/add/",
        merge_dicts(
            {
                "title": "Home EN",
                "slug": "home-en",
                "path": "/en/",
                "static_path": 1,
                "language_code": "en",
                "is_active": 1,
                "menu": "main",
                "page_type": "standard",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )

    assertRedirects(response, "/admin/testapp/page/")

    page = Page.objects.get()
    assert page.slug == "home-en"
    assert page.path == "/en/"  # static_path!

    response = client.get(page.get_absolute_url())
    assertContains(response, "<h1>Home EN</h1>", 1)


@pytest.mark.django_db
def test_add_page(client):
    """Add a page with some content and test rich text cleansing"""
    response = client.post(
        "/admin/testapp/page/add/",
        merge_dicts(
            {
                "title": "Home EN",
                "slug": "home-en",
                "path": "/en/",
                "static_path": 1,
                "language_code": "en",
                "is_active": 1,
                "menu": "main",
                "page_type": "standard",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
            {
                "testapp_richtext_set-0-text": '<span style="font-weight:bold">Hello!</span>',
                "testapp_richtext_set-TOTAL_FORMS": 1,
                "testapp_richtext_set-0-region": "main",
                "testapp_richtext_set-0-ordering": 10,
            },
        ),
    )

    assertRedirects(response, "/admin/testapp/page/")

    page = Page.objects.get()
    assert page.slug == "home-en"
    assert page.path == "/en/"  # static_path!

    response = client.get(page.get_absolute_url())
    assertContains(response, "<h1>Home EN</h1>", 1)
    assertContains(
        response,
        "<strong>Hello!</strong>",
        1,  # HTML cleansing worked.
    )


@pytest.mark.django_db
def test_navigation_and_changelist(client):
    """Test menu template tags and the admin changelist"""
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

    for slug in ("a", "b", "c", "d"):
        Page.objects.create(
            title=f"{slug}-{home_en.language_code}",
            slug=f"{slug}-{home_en.language_code}",
            static_path=False,
            language_code=home_en.language_code,
            is_active=True,
            menu="main",
            parent_id=home_en.pk,
        )
        sub = Page.objects.create(
            title=f"{slug}-{home_de.language_code}",
            slug=f"{slug}-{home_de.language_code}",
            static_path=False,
            language_code=home_de.language_code,
            is_active=True,
            menu="main",
            parent_id=home_de.pk,
        )

        # Create subpage
        Page.objects.create(
            title="sub",
            slug="sub",
            static_path=False,
            language_code=sub.language_code,
            is_active=True,
            menu="main",
            parent_id=sub.pk,
        )

    # Create inactive page
    Page.objects.create(
        title="inactive",
        slug="inactive",
        static_path=False,
        language_code=home_de.language_code,
        is_active=False,
        menu="main",
        parent_id=home_de.pk,
    )

    response = client.get("/en/a-en/")
    assertContains(response, '<a class="active" href="/en/a-en/">a-en</a>', 1)
    assert "/de/" not in response.content.decode()
    # No subnavigation (main nav has a class)
    assert "<nav>" not in response.content.decode()

    response = client.get("/de/b-de/")
    assertContains(response, '<a class="active" href="/de/b-de/">b-de</a>', 1)
    assert "/en/" not in response.content.decode()

    # 4 Subnavigations
    assertContains(response, "<nav>", 4)

    assert "inactive" not in response.content.decode()

    response = client.get("/de/not-exists/")
    assert response.status_code == 404

    # Changelist and filtering
    assertContains(
        client.get("/admin/testapp/page/"),
        'name="_selected_action"',
        15,  # 15 pages
    )
    assertContains(
        client.get(f"/admin/testapp/page/?ancestor={home_de.pk}"),
        'name="_selected_action"',
        10,  # 10 de
    )
    assertContains(
        client.get(f"/admin/testapp/page/?ancestor={home_en.pk}"),
        'name="_selected_action"',
        5,  # 5 en
    )
    assertContains(
        client.get("/admin/testapp/page/"),
        'href="?ancestor=',
        11,  # 2 root pages, 5 de children, 4 en children
    )
    assertRedirects(
        client.get("/admin/testapp/page/?ancestor=abc", follow=False),
        "/admin/testapp/page/?e=1",
    )


@pytest.mark.django_db
def test_snippet(client):
    """Check that snippets have access to the main rendering context
    when using TemplatePluginRenderer"""

    home_en = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )

    snippet = home_en.testapp_snippet_set.create(
        template_name="snippet.html", ordering=10, region="main"
    )

    response = client.get(home_en.get_absolute_url())
    assertContains(response, "<h2>snippet on page home (/en/)</h2>", 1)
    assertContains(response, "<h2>context</h2>", 1)

    snippet.template_name = "this/template/does/not/exist.html"
    snippet.save()
    response = client.get(home_en.get_absolute_url())
    assert response.status_code == 200  # No crash


@pytest.fixture
def duplicated_path_setup():
    """Set up a page structure which leads to duplicated paths when
    sub's parent is set to home"""
    home = Page.objects.create(
        title="home", slug="home", path="/en/", static_path=True, language_code="en"
    )
    Page.objects.create(
        parent=home,
        title="sub",
        slug="sub",
        path="/en/sub/page/",
        static_path=True,
        language_code="en",
    )
    sub = Page.objects.create(title="sub", slug="sub")
    Page.objects.create(parent=sub, title="page", slug="page")

    assert sub.get_absolute_url() == "/sub/"
    assert home.get_absolute_url() == "/en/"

    return home, sub


@pytest.mark.django_db
def test_duplicated_path_save(duplicated_path_setup):
    """Saving the model should not handle the database integrity error"""
    home, sub = duplicated_path_setup

    sub.parent = home
    with transaction.atomic(), pytest.raises(IntegrityError):
        sub.save()


@pytest.mark.django_db
def test_duplicated_path_changeform(client, duplicated_path_setup):
    """The change form should not crash but handle the constraint error"""
    home, sub = duplicated_path_setup

    response = client.post(
        f"/admin/testapp/page/{sub.pk}/change/",
        merge_dicts(
            {
                "parent": home.pk,
                "title": "sub",
                "slug": "sub",
                "language_code": "en",
                "page_type": "standard",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )

    assert response.status_code == 200
    assert re.search(
        r"The page page&#(39|x27);s new path /en/sub/page/ would not be unique.",
        response.content.decode("utf-8"),
    )


@pytest.mark.django_db
def test_path_clash_with_static_subpage_path(client):
    """Test that path clash checks also take some descendants into account"""
    root = Page.objects.create(title="root", slug="root", language_code="en")
    Page.objects.create(parent=root, title="sub2", slug="sub2", language_code="en")

    Page.objects.create(
        parent=root,
        title="sub",
        slug="sub",
        path="/sub2/",
        static_path=True,
        language_code="en",
    )

    response = client.post(
        f"/admin/testapp/page/{root.pk}/change/",
        merge_dicts(
            {
                "parent": "",
                "title": "root-sub",
                "slug": "root-sub",
                "path": "/",
                "static_path": True,
                "language_code": "en",
                "page_type": "standard",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )

    assert response.status_code == 200
    assert re.search(
        r"The page sub2&#(39|x27);s new path /sub2/ would not be unique.",
        response.content.decode("utf-8"),
    )


@pytest.mark.django_db
def test_path_valid_with_static_subpage_path(client):
    """Test that there are no path clashs when subpage has static path"""
    root = Page.objects.create(title="root", slug="root", language_code="en")
    Page.objects.create(
        parent=root,
        title="sub",
        slug="sub",
        static_path=True,
        path="/sub/",
        language_code="en",
    )

    response = client.post(
        f"/admin/testapp/page/{root.pk}/change/",
        merge_dicts(
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )

    assert response.status_code == 200
    assert not re.search(
        r"The page sub&#(39|x27);s new path /sub/ would not be unique.",
        response.content.decode("utf-8"),
    )


@pytest.mark.django_db
def test_i18n_patterns(client):
    """i18n_patterns in ROOT_URLCONF work even with apps_middleware"""
    assertRedirects(client.get("/i18n/"), "/en/i18n/")
    assertRedirects(client.get("/i18n/", HTTP_ACCEPT_LANGUAGE="de"), "/de/i18n/")

    assertContains(client.get("/en/i18n/"), "en")
    assertContains(client.get("/de/i18n/"), "de")


@pytest.mark.django_db
def test_render_plugins(client):
    """Test both render_plugins and render_plugin"""
    page = Page.objects.create(
        is_active=True, title="main", slug="main", page_type="with-sidebar"
    )
    page.testapp_richtext_set.create(ordering=0, region="main", text="<b>main</b>")
    page.testapp_richtext_set.create(
        ordering=0, region="sidebar", text="<i>sidebar</b>"
    )

    response = client.get(page.get_absolute_url())
    assertContains(response, '<div class="main"><b>main</b></div>')
    assertContains(response, '<div class="sidebar"><i>sidebar</b></div>')


@pytest.mark.django_db
def test_add_duplicated_path(client):
    """Non-unique paths should also be detected upon direct addition"""
    Page.objects.create(title="main", slug="main")

    response = client.post(
        "/admin/testapp/page/add/",
        merge_dicts(
            {
                "title": "main",
                "slug": "main",
                "language_code": "en",
                "page_type": "standard",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )
    assertContains(response, "Page with this Path already exists.", status_code=200)


@pytest.mark.django_db
def test_non_empty_static_paths(client):
    """Static paths may not be left empty"""
    response = client.post(
        "/admin/testapp/page/add/",
        merge_dicts(
            {
                "title": "main",
                "slug": "main",
                "language_code": "en",
                "page_type": "standard",
                "static_path": True,
                "path": "",
            },
            zero_management_form_data("testapp_richtext_set"),
            zero_management_form_data("testapp_image_set"),
            zero_management_form_data("testapp_snippet_set"),
            zero_management_form_data("testapp_external_set"),
            zero_management_form_data("testapp_html_set"),
        ),
    )
    assertContains(
        response, "Static paths cannot be empty. Did you mean", status_code=200
    )


def test_reverse():
    """Test all code paths through reverse_fallback and reverse_any"""
    assert reverse_fallback("test", reverse, "not-exists") == "test"
    assert reverse_fallback("test", reverse, "admin:index") == "/admin/"
    assert reverse_any(("not-exists", "admin:index")) == "/admin/"
    assert reverse_any(("not-exists",), fallback="blub") == "blub"
    assert reverse_app("not", "exists", fallback="blub") == "blub"

    with pytest.raises(
        NoReverseMatch,
        match=(
            r"Reverse for any of 'not-exists-1', 'not-exists-2' with"
            r" arguments '\[\]' and keyword arguments '{}' not found."
        ),
    ):
        reverse_any(("not-exists-1", "not-exists-2"))


@pytest.fixture
def prepare_for_move():
    root = Page.objects.create(title="root", slug="root")
    p1 = Page.objects.create(title="p1", slug="p1", parent=root)
    p2 = Page.objects.create(title="p2", slug="p2", parent=root)

    assert [(p.pk, p.parent_id, p.position) for p in Page.objects.all()] == [
        (root.pk, None, 10),
        (p1.pk, root.pk, 10),
        (p2.pk, root.pk, 20),
    ]

    return root, p1, p2


@pytest.mark.django_db
def test_new_location_root(client, prepare_for_move):
    """First child of no parent should move to the root"""
    root, p1, p2 = prepare_for_move

    response = client.post(
        reverse("admin:testapp_page_move", args=(p1.pk,)),
        {"new_location": "0:first"},
    )
    assertRedirects(response, "/admin/testapp/page/")

    assert [(p.pk, p.parent_id, p.position) for p in Page.objects.all()] == [
        (p1.pk, None, 10),
        (root.pk, None, 20),
        (p2.pk, root.pk, 20),
    ]


@pytest.mark.django_db
def test_new_location_child(client, prepare_for_move):
    """First child of a different page, new siblings are pushed back"""
    root, p1, p2 = prepare_for_move

    response = client.post(
        reverse("admin:testapp_page_move", args=(p2.pk,)),
        {"new_location": f"{p1.pk}:first"},
    )
    assertRedirects(response, "/admin/testapp/page/")

    assert [(p.pk, p.parent_id, p.position) for p in Page.objects.all()] == [
        (root.pk, None, 10),
        (p1.pk, root.pk, 10),
        (p2.pk, p1.pk, 10),
    ]


@pytest.mark.django_db
def test_reorder_siblings(client, prepare_for_move):
    """Reordering of siblings"""
    root, p1, p2 = prepare_for_move

    p3 = Page.objects.create(title="p3", slug="p3", parent=root)

    response = client.post(
        reverse("admin:testapp_page_move", args=(p3.pk,)),
        {"new_location": f"{p1.pk}:right"},
    )
    assertRedirects(response, "/admin/testapp/page/")

    assert [(p.pk, p.parent_id, p.position) for p in Page.objects.all()] == [
        (root.pk, None, 10),
        (p1.pk, root.pk, 10),
        (p3.pk, root.pk, 20),
        (p2.pk, root.pk, 30),
    ]


@pytest.mark.django_db
def test_redirects(client):
    """Exercise model and view aspects of redirects"""
    page1 = Page.objects.create(
        title="home",
        slug="home",
        path="/de/",
        static_path=True,
        language_code="de",
        is_active=True,
    )
    page2 = Page.objects.create(
        title="something",
        slug="something",
        path="/something/",
        static_path=True,
        language_code="de",
        is_active=True,
        redirect_to_page=page1,
    )
    page3 = Page.objects.create(
        title="something2",
        slug="something2",
        path="/something2/",
        static_path=True,
        language_code="de",
        is_active=True,
        redirect_to_url="http://example.com/",
    )
    page4 = Page.objects.create(
        title="redirect-does-not-look-like-url",
        slug="redirect-does-not-look-like-url",
        path="/something3/",
        static_path=True,
        language_code="de",
        is_active=True,
        redirect_to_url="looks_like_a_viewname",
    )

    assert page1.get_redirect_url() is None
    assert page2.get_redirect_url() == "/de/"
    assert page3.get_redirect_url() == "http://example.com/"
    assert page4.get_redirect_url() == "looks_like_a_viewname"

    assertRedirects(client.get(page2.get_absolute_url()), page1.get_absolute_url())

    assertRedirects(
        client.get(page3.get_absolute_url(), follow=False),
        "http://example.com/",
        fetch_redirect_response=False,
    )

    assertRedirects(
        client.get(page4.get_absolute_url(), follow=False),
        "/something3/looks_like_a_viewname",
        fetch_redirect_response=False,
    )

    # Everything fine in clean-land
    assert page2.full_clean() is None

    # Both redirects cannot be set at the same time
    with pytest.raises(ValidationError):
        Page(
            title="test",
            slug="test",
            language_code="de",
            redirect_to_page=page1,
            redirect_to_url="nonempty",
        ).full_clean()

    # No chain redirects
    with pytest.raises(ValidationError):
        Page(
            title="test", slug="test", language_code="de", redirect_to_page=page2
        ).full_clean()

    # No redirects to self
    page2.redirect_to_page = page2
    with pytest.raises(ValidationError):
        page2.full_clean()

    # page1 is already the target of a redirect
    page1.redirect_to_url = "http://example.com/"
    with pytest.raises(ValidationError):
        page1.full_clean()


@pytest.mark.django_db
def test_standalone_renderer():
    """The renderer also works when used without a wrapping template"""
    renderer = TemplatePluginRenderer()
    renderer.register_template_renderer(
        HTML, ["renderer/html.html", "renderer/html.html"]
    )

    page = Page.objects.create(page_type="standard")
    HTML.objects.create(parent=page, ordering=10, region="main", html="<b>Hello</b>")

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context()) == "<b>Hello</b>\n"

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context({"outer": "Test"})) == "<b>Hello</b>Test\n"

    regions = Regions.from_item(page, renderer=renderer, timeout=3)
    assert regions.render("main", Context({"outer": "Test2"})) == "<b>Hello</b>Test2\n"

    regions = Regions.from_item(page, renderer=renderer, timeout=3)
    # Output stays the same.
    assert regions.render("main", Context({"outer": "Test3"})) == "<b>Hello</b>Test2\n"

    assert regions.cache_key("main") == f"testapp.page-{page.pk}-main"


@pytest.mark.django_db
def test_plugin_template_instance():
    """The renderer handles template instances, not just template paths etc."""
    renderer = TemplatePluginRenderer()
    renderer.register_template_renderer(HTML, Template("{{ plugin.html|safe }}"))
    page = Page.objects.create(page_type="standard")
    HTML.objects.create(parent=page, ordering=10, region="main", html="<b>Hello</b>")

    regions = Regions.from_item(page, renderer=renderer)
    assert regions.render("main", Context()) == "<b>Hello</b>"
    assert regions.render("main", None) == "<b>Hello</b>"


@pytest.mark.django_db
def test_descendant_update(prepare_for_move):
    """Saving pages with descendants updates descendants too"""
    root, p1, p2 = prepare_for_move  # Fetch again, we need tree_* fields

    root, p1, p2 = Page.objects.with_tree_fields()

    p2.static_path = True
    p2.save()

    with CaptureQueriesContext(connection) as ctx:
        # Only update self
        root.save()
        assert len(ctx.captured_queries) == 1

    p1.refresh_from_db()
    assert p1.path == "/root/p1/"

    with CaptureQueriesContext(connection) as ctx:
        # Update self, fetch two descendants and save them
        root.save(save_descendants=True)
        assert len(ctx.captured_queries) == 4

    root.slug = "blaaa"
    with CaptureQueriesContext(connection) as ctx:
        # Update self, fetch two descendants and save them
        root.save(save_descendants=True)
        assert len(ctx.captured_queries) == 4

    p1.refresh_from_db()
    assert p1.path == "/blaaa/p1/"

    p2.refresh_from_db()
    assert p2.path == "/root/p2/"


@pytest.mark.django_db
def test_move_view_redirect(client):
    """Move view redirects as expected when encountering an invalid PK"""
    # move_view also redirects to index page when encountering invalid
    # object IDs
    response = client.get("/admin/testapp/page/asdf/move/")
    assertRedirects(response, "/admin/")


@pytest.mark.django_db
def test_content_cloning(client):
    """Test that cloning the content works and replaces everything"""
    home_en = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        is_active=True,
        menu="main",
    )

    home_en.testapp_snippet_set.create(
        template_name="snippet.html", ordering=10, region="main"
    )

    home_de = Page.objects.create(
        title="home",
        slug="home",
        path="/de/",
        static_path=True,
        language_code="de",
        is_active=True,
        menu="main",
    )

    home_de.testapp_snippet_set.create(
        template_name="snippet-33.html", ordering=10, region="main"
    )

    response = client.post(
        reverse("admin:testapp_page_clone", args=(home_en.pk,)),
        {"target": home_de.pk, "_set_content": True},
    )
    assertRedirects(response, reverse("admin:testapp_page_change", args=(home_de.pk,)))

    assert list(
        home_de.testapp_snippet_set.values_list("template_name", flat=True)
    ) == ["snippet.html"]


def test_default_type_fallback():
    """The PageTypeMixin falls back to the first template"""
    assert Page(page_type="__notexists").type.key == "standard"


def test_get_absolute_url():
    """Page.get_absolute_url with and without paths"""
    assert Page(path="/test/").get_absolute_url() == "/test/"
    assert Page(path="/").get_absolute_url() == "/"


@pytest.mark.django_db
def test_render_list():
    """render_list, automatic template selection and pagination"""
    for i in range(7):
        Article.objects.create(title=f"Article {i}", category="publications")

    request = RequestFactory().get("/", data={"page": 2})
    response = render_list(
        request, list(Article.objects.all()), model=Article, paginate_by=2
    )

    assert response.template_name == "testapp/article_list.html"
    assert len(response.context_data["object_list"]) == 2
    assert response.context_data["object_list"].number == 2
    assert response.context_data["object_list"].paginator.num_pages == 4


@isolate_apps("testapp")
def test_page_with_missing_ordering():
    """Page subclass without ordering doesn't check out"""

    class Page(AbstractPage):
        class Meta:
            pass

    errors = Page.check()
    expected = [
        Warning(
            "The page subclass isn't ordered by `position`.",
            hint=(
                'Move `AbstractPage` first in the list of classes which your page class inherits or define `ordering = ("position",)` when defining your own `class Meta` on subclassed pages.'
            ),
            obj=Page,
            id="feincms3.W001",
        ),
    ]
    assert errors == expected


@isolate_apps("testapp")
def test_page_with_valid_menu():
    """Using non-identifiers as menu values doesn't work"""

    class Page(AbstractPage, mixins.MenuMixin):
        MENUS = [("", "-"), ("main", "main menu")]

    assert Page.check() == []


@isolate_apps("testapp")
def test_page_with_invalid_menu():
    """Using non-identifiers as menu values doesn't work"""

    class Page(AbstractPage, mixins.MenuMixin):
        MENUS = [("main-menu", "main menu")]

    errors = Page.check()
    assert [error.id for error in errors] == ["feincms3.W005"]


@pytest.mark.django_db
def test_404_language_code_redirect_at_root(client):
    """Root page redirect when a matching page exists"""
    response = client.get("/")
    assert response.status_code == 404

    Page.objects.create(
        title="de",
        slug="de",
        path="/de/",
        static_path=True,
        language_code="de",
        is_active=True,
    )

    response = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assertRedirects(response, "/de/")

    response = client.get("/", HTTP_ACCEPT_LANGUAGE="en")
    assert response.status_code == 404


@pytest.mark.django_db
def test_404_language_code_redirect_deeper(client):
    """No redirects despite using i18n_patterns"""
    Page.objects.create(
        title="de-home",
        slug="de-home",
        path="/de/home/",
        static_path=True,
        language_code="de",
        is_active=True,
    )

    response = client.get("/home/", HTTP_ACCEPT_LANGUAGE="de")
    assert response.status_code == 404

    response = client.get("/", HTTP_ACCEPT_LANGUAGE="en")
    assert response.status_code == 404


@pytest.mark.django_db
def test_404_for_resolvable_path(client):
    """404s from resolvable paths are not handled by the middleware"""
    Page.objects.create(
        title="test",
        slug="test",
        path="/not-found/",
        static_path=True,
        language_code="en",
        is_active=True,
    )

    # 404 from view is forwarded; middleware only acts on non-resolvable
    # paths
    response = client.get("/not-found/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_404_for_resolvable_app_path(client):
    """404s from resolvable app paths are not handled by the middleware"""
    Page.objects.create(
        title="blog",
        slug="blog",
        path="/blog/",
        static_path=True,
        language_code="en",
        is_active=True,
        page_type="blog",
    )
    Page.objects.create(
        title="test",
        slug="test",
        path="/blog/0/",
        static_path=True,
        language_code="en",
        is_active=True,
    )

    response = client.get("/blog/")
    assertContains(response, "<h1>blog</h1>")

    # Page exists at URL but doesn't override the 404 generated by the blog app
    response = client.get("/blog/0/")
    assert response.status_code == 404

    # Our custom 404 handler handles the 404 response in the apps URLconf
    assertContains(response, "My not found handler", status_code=404)


@pytest.mark.django_db
def test_append_slash(client):
    """Requests without slash are redirected if APPEND_SLASH and target exists"""
    Page.objects.create(
        title="home",
        slug="home",
        path="/home/",
        static_path=True,
        language_code="de",
        is_active=True,
        menu="main",
    )

    with override_settings(APPEND_SLASH=True):
        response = client.get("/home")
        assertRedirects(
            response, "/home/", fetch_redirect_response=False, status_code=301
        )

        response = client.get("/blub")
        assert response.status_code == 404

    with override_settings(APPEND_SLASH=False):
        response = client.get("/home")
        assert response.status_code == 404
