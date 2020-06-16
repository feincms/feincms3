from contextlib import contextmanager

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms.models import modelform_factory
from django.template import Context, Template, TemplateSyntaxError
from django.test import Client, RequestFactory, TestCase
from django.urls import set_urlconf
from django.utils.translation import deactivate_all, override

from feincms3.apps import (
    NoReverseMatch,
    apps_urlconf,
    reverse,
    reverse_any,
    reverse_app,
    reverse_fallback,
)
from feincms3.plugins.external import ExternalForm
from feincms3.regions import Regions
from feincms3.renderer import TemplatePluginRenderer
from feincms3.shortcuts import render_list
from feincms3.templatetags.feincms3 import translations

from .models import HTML, Article, External, Page, TranslatedArticle


@contextmanager
def override_urlconf(urlconf):
    set_urlconf(urlconf)
    try:
        yield
    finally:
        set_urlconf(None)


def zero_management_form_data(prefix):
    return {
        "%s-TOTAL_FORMS" % prefix: 0,
        "%s-INITIAL_FORMS" % prefix: 0,
        "%s-MIN_NUM_FORMS" % prefix: 0,
        "%s-MAX_NUM_FORMS" % prefix: 1000,
    }


def merge_dicts(*dicts):
    res = {}
    for d in dicts:
        res.update(d)
    return res


class Test(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.ch", "blabla")
        deactivate_all()

    def login(self):
        client = Client()
        client.force_login(self.user)
        return client

    def test_modules(self):
        """Admin modules are present, necessary JS too"""

        client = self.login()

        response = client.get("/admin/")
        self.assertContains(response, '<a href="/admin/testapp/page/">Pages</a>', 1)

        response = client.get("/admin/testapp/page/")
        self.assertContains(response, "/static/feincms3/box-drawing.css", 1)
        self.assertNotContains(response, "/static/content_editor/content_editor.js")

        response = client.get("/admin/testapp/page/add/")
        self.assertContains(response, "/static/content_editor/content_editor.js", 1)

    def test_add_empty_page(self):
        """Add a page without content, test path generation etc"""
        client = self.login()

        response = client.post(
            "/admin/testapp/page/add/",
            merge_dicts(
                {
                    "title": "Home EN",
                    "slug": "home-en",
                    "path": "/en/",
                    "static_path": 1,
                    "language_code": "en",
                    "application": "",
                    "is_active": 1,
                    "menu": "main",
                    "template_key": "standard",
                },
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
            ),
        )

        self.assertRedirects(response, "/admin/testapp/page/")

        page = Page.objects.get()
        self.assertEqual(page.slug, "home-en")
        self.assertEqual(page.path, "/en/")  # static_path!

        response = client.get(page.get_absolute_url())
        self.assertContains(response, "<h1>Home EN</h1>", 1)

    def test_add_page(self):
        """Add a page with some content and test rich text cleansing"""

        client = self.login()

        response = client.post(
            "/admin/testapp/page/add/",
            merge_dicts(
                {
                    "title": "Home EN",
                    "slug": "home-en",
                    "path": "/en/",
                    "static_path": 1,
                    "language_code": "en",
                    "application": "",
                    "is_active": 1,
                    "menu": "main",
                    "template_key": "standard",
                },
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
                {
                    "testapp_richtext_set-0-text": '<span style="font-weight:bold">Hello!</span>',  # noqa
                    "testapp_richtext_set-TOTAL_FORMS": 1,
                    "testapp_richtext_set-0-region": "main",
                    "testapp_richtext_set-0-ordering": 10,
                },
            ),
        )

        self.assertRedirects(response, "/admin/testapp/page/")

        page = Page.objects.get()
        self.assertEqual(page.slug, "home-en")
        self.assertEqual(page.path, "/en/")  # static_path!

        response = client.get(page.get_absolute_url())
        self.assertContains(response, "<h1>Home EN</h1>", 1)
        self.assertContains(
            response, "<strong>Hello!</strong>", 1  # HTML cleansing worked.
        )

    def test_external_form_validation(self):
        """Test external plugin validation a bit"""

        form_class = modelform_factory(External, form=ExternalForm, fields="__all__")

        # Should not crash if URL not provided (765a6b6b53e)
        form = form_class({})
        self.assertFalse(form.is_valid())

        # Provide an invalid URL
        form = form_class({"url": "http://192.168.250.1:65530"})
        self.assertFalse(form.is_valid())
        self.assertIn(
            "<li>Unable to fetch HTML for this URL, sorry!</li>", "%s" % form.errors
        )

    def test_navigation_and_changelist(self):
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
                title="%s-%s" % (slug, home_en.language_code),
                slug="%s-%s" % (slug, home_en.language_code),
                static_path=False,
                language_code=home_en.language_code,
                is_active=True,
                menu="main",
                parent_id=home_en.pk,
            )
            sub = Page.objects.create(
                title="%s-%s" % (slug, home_de.language_code),
                slug="%s-%s" % (slug, home_de.language_code),
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

        response_en = self.client.get("/en/a-en/")
        self.assertContains(
            response_en, '<a class="active" href="/en/a-en/">a-en</a>', 1
        )
        self.assertNotContains(response_en, "/de/")
        # No subnavigation (main nav has a class)
        self.assertNotContains(response_en, "<nav>")

        response_de = self.client.get("/de/b-de/")
        self.assertContains(
            response_de, '<a class="active" href="/de/b-de/">b-de</a>', 1
        )
        self.assertNotContains(response_de, "/en/")

        # 4 Subnavigations
        self.assertContains(response_de, "<nav>", 4)

        self.assertNotContains(response_de, "inactive")

        response_404 = self.client.get("/de/not-exists/")
        self.assertContains(response_404, "<h1>Page not found</h1>", 1, status_code=404)
        self.assertContains(response_404, 'href="/de/', 8, status_code=404)

        # Changelist and filtering
        client = self.login()
        self.assertContains(
            client.get("/admin/testapp/page/"),
            'name="_selected_action"',
            15,  # 15 pages
        )
        self.assertContains(
            client.get("/admin/testapp/page/?ancestor=%s" % home_de.pk),
            'name="_selected_action"',
            10,  # 10 de
        )
        self.assertContains(
            client.get("/admin/testapp/page/?ancestor=%s" % home_en.pk),
            'name="_selected_action"',
            5,  # 5 en
        )
        self.assertContains(
            client.get("/admin/testapp/page/"),
            'href="?ancestor=',
            11,  # 2 root pages, 5 de children, 4 en children
        )
        self.assertRedirects(
            client.get("/admin/testapp/page/?ancestor=abc", follow=False),
            "/admin/testapp/page/?e=1",
        )

    def test_apps(self):
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
                    application=app,
                    parent_id=root.pk,
                )

        for i in range(7):
            for category in ("publications", "blog"):
                Article.objects.create(title="%s %s" % (category, i), category=category)

        self.assertContains(self.client.get("/de/blog/all/"), 'class="article"', 7)
        self.assertContains(self.client.get("/de/blog/?page=2"), 'class="article"', 2)
        self.assertContains(
            self.client.get("/de/blog/?page=42"),
            'class="article"',
            2,  # Last page with instances (2nd)
        )
        self.assertContains(
            self.client.get("/de/blog/?page=invalid"),
            'class="article"',
            5,  # First page
        )

        response = self.client.get("/de/blog/")
        self.assertContains(response, 'class="article"', 5)

        response = self.client.get("/en/publications/")
        self.assertContains(response, 'class="article"', 5)

        with override_urlconf(apps_urlconf()):
            article = Article.objects.order_by("pk").first()
            with override("de"):
                self.assertEqual(
                    article.get_absolute_url(), "/de/publications/%s/" % article.pk
                )

            with override("en"):
                self.assertEqual(
                    article.get_absolute_url(), "/en/publications/%s/" % article.pk
                )

                # The german URL is returned when specifying the ``languages``
                # list explicitly.
                self.assertEqual(
                    reverse_app(
                        (article.category, "articles"),
                        "article-detail",
                        kwargs={"pk": article.pk},
                        languages=["de", "en"],
                    ),
                    "/de/publications/%s/" % article.pk,
                )

        response = self.client.get("/de/publications/%s/" % article.pk)
        self.assertContains(response, "<h1>publications 0</h1>", 1)

        # The exact value of course does not matter, just the fact that the
        # value does not change all the time.
        self.assertEqual(apps_urlconf(), "urlconf_fe9552a8363ece1f7fcf4970bf575a47")

    def _apps_validation_models(self, home_path=None):
        home = Page.objects.create(
            title="home",
            slug="home",
            path=home_path or "/en/",
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
            application="blog",
            parent=home,
        )
        return home, blog

    def test_apps_leaf(self):
        """Test that applications are leaf nodes"""

        home, blog = self._apps_validation_models()
        home.application = "blog"
        with self.assertRaises(ValidationError) as cm:
            home.full_clean()

        self.assertEqual(
            cm.exception.error_dict["application"][0].message,
            "Apps may not have any descendants in the tree.",
        )

    def test_apps_no_descendants(self):
        """Test that apps have no descendants"""

        home, blog = self._apps_validation_models()
        third = Page(title="third", slug="third", language_code="en", parent=blog)
        with self.assertRaises(ValidationError) as cm:
            third.full_clean()

        self.assertEqual(
            cm.exception.error_dict["parent"][0].message,
            "Invalid parent: Apps may not have any descendants.",
        )

    def test_apps_duplicate(self):
        """Test that apps cannot be added twice with the exact same configuration"""
        home, blog = self._apps_validation_models()
        _, blog2 = self._apps_validation_models("/en2/")

        with self.assertRaises(ValidationError) as cm:
            blog2.full_clean()

        self.assertEqual(
            cm.exception.error_dict["application"][0].message,
            "This exact app already exists.",
        )

    def test_apps_required_fields(self):
        home = Page(
            title="home",
            slug="home",
            path="/en/",
            static_path=True,
            language_code="en",
            is_active=True,
            menu="main",
            application="stuff-with-required",
        )
        with self.assertRaises(ValidationError) as cm:
            home.full_clean(exclude=["not_editable"])

        self.assertEqual(
            cm.exception.error_dict["optional"][0].message,
            "This field is required for the application stuff-with-required.",
        )

        home.optional = 1
        home.not_editable = 2
        home.full_clean(exclude=["not_editable"])

    def test_apps_cloning_validation(self):
        """Checks that the target is properly validated when cloning"""
        home, blog = self._apps_validation_models()
        client = self.login()

        clone_url = reverse("admin:testapp_page_clone", args=(blog.pk,))

        response = client.get(clone_url)
        self.assertContains(response, "_set_content")
        self.assertContains(response, "set_application")

        response = client.post(clone_url, {"target": home.pk, "set_application": True})
        self.assertContains(response, "Apps may not have any descendants in the tree.")

        # The other way round works
        clone_url = reverse("admin:testapp_page_clone", args=(home.pk,))

        response = client.post(clone_url, {"target": blog.pk, "set_application": True})
        self.assertRedirects(
            response, reverse("admin:testapp_page_change", args=(blog.pk,))
        )

        # No apps in tree anymore
        self.assertEqual(Page.objects.exclude(application="").count(), 0)

    def test_snippet(self):
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

        home_en.testapp_snippet_set.create(
            template_name="snippet.html", ordering=10, region="main"
        )

        response = self.client.get(home_en.get_absolute_url())
        self.assertContains(response, "<h2>snippet on page home (/en/)</h2>", 1)
        self.assertContains(response, "<h2>context</h2>", 1)

    def duplicated_path_setup(self):
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

        self.assertEqual(sub.get_absolute_url(), "/sub/")
        self.assertEqual(home.get_absolute_url(), "/en/")

        return home, sub

    def test_duplicated_path_save(self):
        """Saving the model should not handle the database integrity error"""

        home, sub = self.duplicated_path_setup()

        sub.parent = home
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                sub.save()

    def test_duplicated_path_changeform(self):
        """The change form should not crash but handle the constraint error"""

        client = self.login()
        home, sub = self.duplicated_path_setup()

        response = client.post(
            "/admin/testapp/page/%s/change/" % sub.pk,
            merge_dicts(
                {
                    "parent": home.pk,
                    "title": "sub",
                    "slug": "sub",
                    "language_code": "en",
                    "template_key": "standard",
                },
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.content.decode("utf-8"),
            "The page page&#(39|x27);s new path /en/sub/page/ would not be unique.",
        )

    def test_path_clash_with_static_subpage_path(self):
        """Test that path clash checks also take some descendants into account"""
        client = self.login()
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
            "/admin/testapp/page/%s/change/" % root.pk,
            merge_dicts(
                {
                    "parent": "",
                    "title": "root-sub",
                    "slug": "root-sub",
                    "path": "/",
                    "static_path": True,
                    "language_code": "en",
                    "template_key": "standard",
                },
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
            ),
        )

        # print(response, response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.content.decode("utf-8"),
            r"The page sub2&#(39|x27);s new path /sub2/ would not be unique.",
        )

    def test_path_valid_with_static_subpage_path(self):
        """Test that there are no path clashs when subpage has static path"""
        client = self.login()
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
            "/admin/testapp/page/%s/change/" % root.pk,
            merge_dicts(
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotRegex(
            response.content.decode("utf-8"),
            r"The page sub&#(39|x27);s new path /sub/ would not be unique.",
        )

    def test_i18n_patterns(self):
        """i18n_patterns in ROOT_URLCONF work even with apps_middleware"""

        self.assertRedirects(self.client.get("/i18n/"), "/en/i18n/")
        self.assertRedirects(
            self.client.get("/i18n/", HTTP_ACCEPT_LANGUAGE="de"), "/de/i18n/"
        )

        self.assertContains(self.client.get("/en/i18n/"), "en")
        self.assertContains(self.client.get("/de/i18n/"), "de")

    def test_render_plugins(self):
        """Test both render_plugins and render_plugin"""

        page = Page.objects.create(
            is_active=True, title="main", slug="main", template_key="with-sidebar"
        )
        page.testapp_richtext_set.create(ordering=0, region="main", text="<b>main</b>")
        page.testapp_richtext_set.create(
            ordering=0, region="sidebar", text="<i>sidebar</b>"
        )

        response = self.client.get(page.get_absolute_url())
        self.assertContains(response, '<div class="main"><b>main</b></div>')
        self.assertContains(response, '<div class="sidebar"><i>sidebar</b></div>')

    def test_add_duplicated_path(self):
        """Non-unique paths should also be detected upon direct addition"""

        Page.objects.create(title="main", slug="main")

        client = self.login()
        response = client.post(
            "/admin/testapp/page/add/",
            merge_dicts(
                {
                    "title": "main",
                    "slug": "main",
                    "language_code": "en",
                    "application": "",
                    "template_key": "standard",
                },
                zero_management_form_data("testapp_richtext_set"),
                zero_management_form_data("testapp_image_set"),
                zero_management_form_data("testapp_snippet_set"),
                zero_management_form_data("testapp_external_set"),
                zero_management_form_data("testapp_html_set"),
            ),
        )
        self.assertContains(
            response, "Page with this Path already exists.", status_code=200
        )

    def test_non_empty_static_paths(self):
        """Static paths may not be left empty"""
        client = self.login()
        response = client.post(
            "/admin/testapp/page/add/",
            merge_dicts(
                {
                    "title": "main",
                    "slug": "main",
                    "language_code": "en",
                    "application": "",
                    "template_key": "standard",
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
        self.assertContains(
            response, "Static paths cannot be empty. Did you mean", status_code=200
        )

    def test_reverse(self):
        """Test all code paths through reverse_fallback and reverse_any"""

        self.assertEqual(reverse_fallback("test", reverse, "not-exists"), "test")
        self.assertEqual(reverse_fallback("test", reverse, "admin:index"), "/admin/")
        self.assertEqual(reverse_any(("not-exists", "admin:index")), "/admin/")
        with self.assertRaisesRegex(
            NoReverseMatch,
            r"Reverse for any of 'not-exists-1', 'not-exists-2' with"
            r" arguments '\[\]' and keyword arguments '{}' not found.",
        ):
            reverse_any(("not-exists-1", "not-exists-2"))

    def prepare_for_move(self):
        root = Page.objects.create(title="root", slug="root")
        p1 = Page.objects.create(title="p1", slug="p1", parent=root)
        p2 = Page.objects.create(title="p2", slug="p2", parent=root)

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [(root.pk, None, 10), (p1.pk, root.pk, 10), (p2.pk, root.pk, 20)],
        )

        return root, p1, p2

    def test_move_to_root_last(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        response = client.get(reverse("admin:testapp_page_move", args=(p1.pk,)))
        self.assertContains(response, "*** p1", 1)
        self.assertContains(response, "--- p2", 1)
        self.assertContains(response, 'name="_save"', 1)

        response = client.post(
            reverse("admin:testapp_page_move", args=(p1.pk,)),
            {"move_to": "last", "of": ""},
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [(root.pk, None, 10), (p2.pk, root.pk, 20), (p1.pk, None, 20)],
        )

    def test_move_to_root_first(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        client.post(
            reverse("admin:testapp_page_move", args=(p2.pk,)),
            {"move_to": "first", "of": ""},
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [(p2.pk, None, 10), (root.pk, None, 20), (p1.pk, root.pk, 10)],
        )

    def test_move_to_child(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        client.post(
            reverse("admin:testapp_page_move", args=(p2.pk,)),
            {"move_to": "first", "of": p1.pk},
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [(root.pk, None, 10), (p1.pk, root.pk, 10), (p2.pk, p1.pk, 10)],
        )

    def test_invalid_move(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        response = client.post(reverse("admin:testapp_page_move", args=(root.pk,)), {})
        self.assertContains(response, "This field is required.", 1)

        response = client.post(
            reverse("admin:testapp_page_move", args=(root.pk,)),
            {"move_to": "first", "of": p1.pk},
        )
        self.assertContains(
            response,
            "Select a valid choice. That choice is not one of the available choices.",  # noqa
        )

        response = client.post(
            reverse("admin:testapp_page_move", args=(root.pk,)),
            {"move_to": "first", "of": root.pk},
        )
        self.assertContains(
            response, "Cannot move node to a position relative to itself."
        )

    def test_reorder_siblings(self):
        root, p1, p2 = self.prepare_for_move()

        p3 = Page.objects.create(title="p3", slug="p3", parent=root)
        client = self.login()

        client.post(
            reverse("admin:testapp_page_move", args=(p3.pk,)),
            {"move_to": "right", "of": p1.pk},
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p1.pk, root.pk, 10),
                (p3.pk, root.pk, 20),
                (p2.pk, root.pk, 30),
            ],
        )

        client.post(
            reverse("admin:testapp_page_move", args=(p3.pk,)),
            {"move_to": "left", "of": p1.pk},
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p3.pk, root.pk, 10),
                (p1.pk, root.pk, 20),
                (p2.pk, root.pk, 30),
            ],
        )

    def test_invalid_parent(self):
        root, p1, p2 = self.prepare_for_move()
        p1.application = "blog"
        p1.save()

        p2 = Page.objects.get(pk=p2.pk)
        p2.parent_id = p1.pk

        # Apps may not have descendants
        self.assertRaises(ValidationError, p2.full_clean)

        client = self.login()
        response = client.post(
            reverse("admin:testapp_page_move", args=(p2.pk,)),
            {"move_to": "first", "of": p1.pk},
        )

        self.assertContains(
            response,
            "<li>Invalid parent: Apps may not have any descendants.</li>",
            status_code=200,
        )

    def test_redirects(self):
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

        self.assertRedirects(
            self.client.get(page2.get_absolute_url()), page1.get_absolute_url()
        )

        self.assertRedirects(
            self.client.get(page3.get_absolute_url(), follow=False),
            "http://example.com/",
            fetch_redirect_response=False,
        )

        # Everything fine in clean-land
        self.assertIs(page2.full_clean(), None)

        # Both redirects cannot be set at the same time
        self.assertRaises(
            ValidationError,
            lambda: Page(
                title="test",
                slug="test",
                language_code="de",
                redirect_to_page=page1,
                redirect_to_url="nonempty",
            ).full_clean(),
        )

        # No chain redirects
        self.assertRaises(
            ValidationError,
            lambda: Page(
                title="test", slug="test", language_code="de", redirect_to_page=page2
            ).full_clean(),
        )

        # No redirects to self
        page2.redirect_to_page = page2
        self.assertRaises(ValidationError, page2.full_clean)

        # page1 is already the target of a redirect
        page1.redirect_to_url = "http://example.com/"
        self.assertRaises(ValidationError, page1.full_clean)

    def test_standalone_renderer(self):
        """The renderer also works when used without a wrapping template"""

        renderer = TemplatePluginRenderer()
        renderer.register_template_renderer(
            HTML, ["renderer/html.html", "renderer/html.html"]
        )

        page = Page.objects.create(template_key="standard")
        HTML.objects.create(
            parent=page, ordering=10, region="main", html="<b>Hello</b>"
        )

        regions = Regions.from_item(page, renderer=renderer)
        self.assertEqual(regions.render("main", Context()), "<b>Hello</b>\n")

        regions = Regions.from_item(page, renderer=renderer)
        self.assertEqual(
            regions.render("main", Context({"outer": "Test"})), "<b>Hello</b>Test\n"
        )

        regions = Regions.from_item(page, renderer=renderer, timeout=3)
        self.assertEqual(
            regions.render("main", Context({"outer": "Test2"})), "<b>Hello</b>Test2\n"
        )
        regions = Regions.from_item(page, renderer=renderer, timeout=3)
        # Output stays the same.
        self.assertEqual(
            regions.render("main", Context({"outer": "Test3"})), "<b>Hello</b>Test2\n"
        )

        self.assertEqual(regions.cache_key("main"), "testapp.page-%s-main" % page.pk)

    def test_plugin_template_instance(self):
        renderer = TemplatePluginRenderer()
        renderer.register_template_renderer(HTML, Template("{{ plugin.html|safe }}"))
        page = Page.objects.create(template_key="standard")
        HTML.objects.create(
            parent=page, ordering=10, region="main", html="<b>Hello</b>"
        )

        regions = Regions.from_item(page, renderer=renderer)
        self.assertEqual(regions.render("main", Context()), "<b>Hello</b>")
        self.assertEqual(regions.render("main", None), "<b>Hello</b>")

    def test_reverse_app_tag(self):
        Page.objects.create(
            title="blog",
            slug="blog",
            static_path=False,
            language_code="en",
            is_active=True,
            application="blog",
        )

        tests = [
            ("{% reverse_app 'blog' 'article-detail' pk=42 %}", "/blog/42/", {}),
            (
                "{% reverse_app 'blog' 'article-detail' pk=42 fallback='/a/' %}",
                "/blog/42/",
                {},
            ),
            (
                "{% reverse_app namespaces 'article-detail' pk=42 fallback='/a/' as a %}{{ a }}",  # noqa
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
                self.assertEqual(t.render(Context(ctx)).strip(), out)

            self.assertRaises(
                NoReverseMatch,
                Template("{% load feincms3 %}{% reverse_app 'a' 'a' %}").render,
                Context(),
            )

    def test_reverse_app_failures(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template("{% load feincms3 %}{% reverse_app %}")
        self.assertEqual(
            str(cm.exception),
            "'reverse_app' takes at least two arguments, a namespace and a URL pattern name.",  # noqa
        )

    def test_descendant_update(self):
        self.prepare_for_move()
        root, p1, p2 = list(Page.objects.all())

        p2.static_path = True
        p2.save()

        with self.assertNumQueries(1):
            # Only update self
            root.save()

        p1.refresh_from_db()
        self.assertEqual(p1.path, "/root/p1/")

        with self.assertNumQueries(4):
            # Update self, fetch two descendants and save them
            root.save(save_descendants=True)

        root.slug = "blaaa"
        with self.assertNumQueries(4):
            # Update self, fetch two descendants and save them
            root.save(save_descendants=True)

        p1.refresh_from_db()
        self.assertEqual(p1.path, "/blaaa/p1/")

        p2.refresh_from_db()
        self.assertEqual(p2.path, "/root/p2/")

    def test_move_view_redirect(self):
        client = self.login()
        # move_view also redirects to index page when encountering invalid
        # object IDs
        response = client.get("/admin/testapp/page/asdf/move/")
        self.assertRedirects(response, "/admin/")

    def test_content_cloning(self):
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

        client = self.login()
        response = client.post(
            reverse("admin:testapp_page_clone", args=(home_en.pk,)),
            {"target": home_de.pk, "_set_content": True},
        )
        # print(response.content.decode("utf-8"))
        self.assertRedirects(
            response, reverse("admin:testapp_page_change", args=(home_de.pk,))
        )

        self.assertEqual(
            list(home_de.testapp_snippet_set.values_list("template_name", flat=True)),
            ["snippet.html"],
        )

    def test_default_template_fallback(self):
        template = Page(template_key="__notexists").template
        self.assertEqual(template.key, "standard")

    def test_apps_urlconf_no_apps(self):
        self.assertEqual(apps_urlconf(apps=[]), "testapp.urls")

    def test_get_absolute_url(self):
        self.assertEqual(Page(path="/test/").get_absolute_url(), "/test/")
        self.assertEqual(Page(path="/").get_absolute_url(), "/")

    def test_render_list(self):
        for i in range(7):
            Article.objects.create(title="Article %s" % i, category="publications")

        request = RequestFactory().get("/", data={"page": 2})
        response = render_list(
            request, list(Article.objects.all()), model=Article, paginate_by=2
        )

        self.assertEqual(response.template_name, "testapp/article_list.html")
        self.assertEqual(len(response.context_data["object_list"]), 2)
        self.assertEqual(response.context_data["object_list"].number, 2)
        self.assertEqual(response.context_data["object_list"].paginator.num_pages, 4)

    def test_language_and_translation_of_mixin(self):
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

        self.assertEqual(set(original.translations()), {original, translation})
        self.assertEqual(set(translation.translations()), {original, translation})

        self.assertEqual(
            [
                language["object"]
                for language in translations(translation.translations())
            ],
            [original, translation, None],
        )

        original.delete()
        translation.refresh_from_db()

        self.assertEqual(set(translation.translations()), set())

    def test_language_and_translation_of_mixin_in_app(self):
        Page.objects.create(
            title="home-en",
            slug="home-en",
            language_code="en",
            is_active=True,
            application="translated-articles",
        )
        Page.objects.create(
            title="home-de",
            slug="home-de",
            language_code="de",
            is_active=True,
            application="translated-articles",
        )

        original = TranslatedArticle.objects.create(title="News", language_code="en")
        translated = TranslatedArticle.objects.create(
            title="Neues", language_code="de", translation_of=original
        )

        self.assertEqual(
            [language["object"] for language in translations(original.translations())],
            [original, translated, None],
        )

        with override_urlconf(apps_urlconf()):
            self.assertEqual(
                original.get_absolute_url(), "/home-en/{}/".format(original.pk)
            )
            self.assertEqual(
                translated.get_absolute_url(), "/home-de/{}/".format(translated.pk)
            )
