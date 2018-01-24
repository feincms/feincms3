from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.forms.models import modelform_factory
from django.template import Context
from django.test import Client, TestCase
from django.utils import six
from django.utils.translation import deactivate_all, override

from feincms3.apps import (
    NoReverseMatch, apps_urlconf, reverse, reverse_any, reverse_fallback,
)
from feincms3.plugins.external import ExternalForm
from feincms3.renderer import TemplatePluginRenderer
from feincms3.utils import concrete_model, iterate_subclasses, positional

from .models import HTML, Article, External, Page


def zero_management_form_data(prefix):
    return {
        '%s-TOTAL_FORMS' % prefix: 0,
        '%s-INITIAL_FORMS' % prefix: 0,
        '%s-MIN_NUM_FORMS' % prefix: 0,
        '%s-MAX_NUM_FORMS' % prefix: 1000,
    }


def merge_dicts(*dicts):
    res = {}
    for d in dicts:
        res.update(d)
    return res


def monkeypatches():
    import django

    if django.VERSION >= (2, 1):
        from ckeditor.widgets import CKEditorWidget

        _original_render = CKEditorWidget.render

        def render(self, name, value, attrs=None, renderer=None):
            return _original_render(self, name, value, attrs=attrs)

        CKEditorWidget.render = render


class Test(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            'admin', 'admin@test.ch', 'blabla')
        deactivate_all()
        monkeypatches()

    def login(self):
        client = Client()
        client.force_login(self.user)
        return client

    def test_modules(self):
        """Admin modules are present, necessary JS too"""

        client = self.login()

        response = client.get('/admin/')
        self.assertContains(
            response,
            '<a href="/admin/testapp/page/">Pages</a>',
            1,
        )

        response = client.get('/admin/testapp/page/')
        self.assertContains(
            response,
            '/static/feincms3/box-drawing.css',
            1,
        )
        self.assertNotContains(
            response,
            '/static/content_editor/content_editor.js',
        )

        response = client.get('/admin/testapp/page/add/')
        self.assertContains(
            response,
            '/static/content_editor/content_editor.js',
            1,
        )

    def test_add_empty_page(self):
        """Add a page without content, test path generation etc"""
        client = self.login()

        response = client.post(
            '/admin/testapp/page/add/',
            merge_dicts(
                {
                    'title': 'Home EN',
                    'slug': 'home-en',
                    'path': '/en/',
                    'static_path': 1,
                    'language_code': 'en',
                    'application': '',
                    'is_active': 1,
                    'menu': 'main',
                    'template_key': 'standard',
                },
                zero_management_form_data('testapp_richtext_set'),
                zero_management_form_data('testapp_image_set'),
                zero_management_form_data('testapp_snippet_set'),
                zero_management_form_data('testapp_external_set'),
                zero_management_form_data('testapp_html_set'),
            ),
        )

        self.assertRedirects(
            response,
            '/admin/testapp/page/',
        )

        page = Page.objects.get()
        self.assertEqual(page.slug, 'home-en')
        self.assertEqual(page.path, '/en/')  # static_path!

        response = client.get(page.get_absolute_url())
        self.assertContains(
            response,
            '<h1>Home EN</h1>',
            1,
        )

    def test_add_page(self):
        """Add a page with some content and test rich text cleansing"""

        client = self.login()

        response = client.post(
            '/admin/testapp/page/add/',
            merge_dicts(
                {
                    'title': 'Home EN',
                    'slug': 'home-en',
                    'path': '/en/',
                    'static_path': 1,
                    'language_code': 'en',
                    'application': '',
                    'is_active': 1,
                    'menu': 'main',
                    'template_key': 'standard',
                },
                zero_management_form_data('testapp_richtext_set'),
                zero_management_form_data('testapp_image_set'),
                zero_management_form_data('testapp_snippet_set'),
                zero_management_form_data('testapp_external_set'),
                zero_management_form_data('testapp_html_set'),
                {
                    'testapp_richtext_set-0-text': '<span style="font-weight:bold">Hello!</span>',  # noqa
                    'testapp_richtext_set-TOTAL_FORMS': 1,
                    'testapp_richtext_set-0-region': 'main',
                    'testapp_richtext_set-0-ordering': 10,
                },
            ),
        )

        self.assertRedirects(
            response,
            '/admin/testapp/page/',
        )

        page = Page.objects.get()
        self.assertEqual(page.slug, 'home-en')
        self.assertEqual(page.path, '/en/')  # static_path!

        response = client.get(page.get_absolute_url())
        self.assertContains(
            response,
            '<h1>Home EN</h1>',
            1,
        )
        self.assertContains(
            response,
            '<strong>Hello!</strong>',  # HTML cleansing worked.
            1,
        )

    def test_external_form_validation(self):
        """Test external plugin validation a bit"""

        form_class = modelform_factory(
            External,
            form=ExternalForm,
            fields='__all__',
        )

        # Should not crash if URL not provided (765a6b6b53e)
        form = form_class({})
        self.assertFalse(form.is_valid())

        # Provide an invalid URL
        form = form_class({'url': 'http://192.168.250.1:65530'})
        self.assertFalse(form.is_valid())
        self.assertIn(
            '<li>Unable to fetch HTML for this URL, sorry!</li>',
            '%s' % form.errors)

    def test_navigation_and_changelist(self):
        """Test menu template tags and the admin changelist"""

        home_de = Page.objects.create(
            title='home',
            slug='home',
            path='/de/',
            static_path=True,
            language_code='de',
            is_active=True,
            menu='main',
        )
        home_en = Page.objects.create(
            title='home',
            slug='home',
            path='/en/',
            static_path=True,
            language_code='en',
            is_active=True,
            menu='main',
        )

        for slug in ('a', 'b', 'c', 'd'):
            Page.objects.create(
                title='%s-%s' % (slug, home_en.language_code),
                slug='%s-%s' % (slug, home_en.language_code),
                static_path=False,
                language_code=home_en.language_code,
                is_active=True,
                menu='main',
                parent_id=home_en.pk,
            )
            sub = Page.objects.create(
                title='%s-%s' % (slug, home_de.language_code),
                slug='%s-%s' % (slug, home_de.language_code),
                static_path=False,
                language_code=home_de.language_code,
                is_active=True,
                menu='main',
                parent_id=home_de.pk,
            )

            # Create subpage
            Page.objects.create(
                title='sub',
                slug='sub',
                static_path=False,
                language_code=sub.language_code,
                is_active=True,
                menu='main',
                parent_id=sub.pk,
            )

        # Create inactive page
        Page.objects.create(
            title='inactive',
            slug='inactive',
            static_path=False,
            language_code=home_de.language_code,
            is_active=False,
            menu='main',
            parent_id=home_de.pk,
        )

        response_en = self.client.get('/en/a-en/')
        self.assertContains(
            response_en,
            '<a class="active" href="/en/a-en/">a-en</a>',
            1,
        )
        self.assertNotContains(
            response_en,
            '/de/',
        )
        # No subnavigation (main nav has a class)
        self.assertNotContains(
            response_en,
            '<nav>',
        )

        response_de = self.client.get('/de/b-de/')
        self.assertContains(
            response_de,
            '<a class="active" href="/de/b-de/">b-de</a>',
            1,
        )
        self.assertNotContains(
            response_de,
            '/en/',
        )

        # 4 Subnavigations
        self.assertContains(
            response_de,
            '<nav>',
            4,
        )

        self.assertNotContains(
            response_de,
            'inactive',
        )

        response_404 = self.client.get('/de/not-exists/')
        self.assertContains(
            response_404,
            '<h1>Page not found</h1>',
            1,
            status_code=404,
        )
        self.assertContains(
            response_404,
            'href="/de/',
            8,
            status_code=404,
        )

        # Changelist and filtering
        client = self.login()
        self.assertContains(
            client.get('/admin/testapp/page/'),
            'name="_selected_action"',
            15,  # 15 pages
        )
        self.assertContains(
            client.get('/admin/testapp/page/?ancestor=%s' % home_de.pk),
            'name="_selected_action"',
            10,  # 10 de
        )
        self.assertContains(
            client.get('/admin/testapp/page/?ancestor=%s' % home_en.pk),
            'name="_selected_action"',
            5,  # 5 en
        )
        self.assertContains(
            client.get('/admin/testapp/page/'),
            'href="?ancestor=',
            11,  # 2 root pages, 5 de children, 4 en children
        )
        self.assertRedirects(
            client.get('/admin/testapp/page/?ancestor=abc', follow=False),
            '/admin/testapp/page/?e=1',
        )

    def test_apps(self):
        """Article app test (two instance namespaces, two languages)"""

        home_de = Page.objects.create(
            title='home',
            slug='home',
            path='/de/',
            static_path=True,
            language_code='de',
            is_active=True,
            menu='main',
        )
        home_en = Page.objects.create(
            title='home',
            slug='home',
            path='/en/',
            static_path=True,
            language_code='en',
            is_active=True,
            menu='main',
        )

        for root in (home_de, home_en):
            for app in ('blog', 'publications'):
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
            for category in ('publications', 'blog'):
                Article.objects.create(
                    title='%s %s' % (category, i),
                    category=category,
                )

        self.assertContains(
            self.client.get('/de/blog/all/'),
            'class="article"',
            7,
        )
        self.assertContains(
            self.client.get('/de/blog/?page=2'),
            'class="article"',
            2,
        )
        self.assertContains(
            self.client.get('/de/blog/?page=42'),
            'class="article"',
            2,  # Last page with instances (2nd)
        )
        self.assertContains(
            self.client.get('/de/blog/?page=invalid'),
            'class="article"',
            5,  # First page
        )

        response = self.client.get('/de/blog/')
        self.assertContains(
            response,
            'class="article"',
            5,
        )

        response = self.client.get('/en/publications/')
        self.assertContains(
            response,
            'class="article"',
            5,
        )

        article = Article.objects.order_by('pk').first()
        with override('de'):
            self.assertEqual(
                article.get_absolute_url(),
                '/de/publications/%s/' % article.pk,
            )

        with override('en'):
            self.assertEqual(
                article.get_absolute_url(),
                '/en/publications/%s/' % article.pk,
            )

        response = self.client.get('/de/publications/%s/' % article.pk)
        self.assertContains(
            response,
            '<h1>publications 0</h1>',
            1,
        )

        # The exact value of course does not matter, just the fact that the
        # value does not change all the time.
        self.assertEqual(
            apps_urlconf(),
            'urlconf_fe9552a8363ece1f7fcf4970bf575a47',
        )

    def test_snippet(self):
        """Check that snippets have access to the main rendering context
        when using TemplatePluginRenderer"""

        home_en = Page.objects.create(
            title='home',
            slug='home',
            path='/en/',
            static_path=True,
            language_code='en',
            is_active=True,
            menu='main',
        )

        home_en.testapp_snippet_set.create(
            template_name='snippet.html',
            ordering=10,
            region='main',
        )

        response = self.client.get(home_en.get_absolute_url())
        self.assertContains(
            response,
            '<h2>snippet on page home (/en/)</h2>',
            1,
        )
        self.assertContains(
            response,
            '<h2>context</h2>',
            1,
        )

    def duplicated_path_setup(self):
        """Set up a page structure which leads to duplicated paths when
        sub's parent is set to home"""

        home = Page.objects.create(
            title='home',
            slug='home',
            path='/en/',
            static_path=True,
            language_code='en',
        )
        Page.objects.create(
            parent=home,
            title='sub',
            slug='sub',
            path='/en/sub/page/',
            static_path=True,
            language_code='en',
        )
        sub = Page.objects.create(
            title='sub',
            slug='sub',
        )
        Page.objects.create(
            parent=sub,
            title='page',
            slug='page',
        )

        self.assertEqual(sub.get_absolute_url(), '/sub/')
        self.assertEqual(home.get_absolute_url(), '/en/')

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
            '/admin/testapp/page/%s/change/' % sub.pk,
            merge_dicts(
                {
                    'parent': home.pk,
                    'title': 'sub',
                    'slug': 'sub',
                    'language_code': 'en',
                    'template_key': 'standard',
                },
                zero_management_form_data('testapp_richtext_set'),
                zero_management_form_data('testapp_image_set'),
                zero_management_form_data('testapp_snippet_set'),
                zero_management_form_data('testapp_external_set'),
                zero_management_form_data('testapp_html_set'),
            ),
        )

        self.assertContains(
            response,
            'The page page&#39;s new path /en/sub/page/ would not be unique.',
            1,
        )

    def test_i18n_patterns(self):
        """i18n_patterns in ROOT_URLCONF work even with AppsMiddleware"""

        self.assertRedirects(
            self.client.get('/i18n/'),
            '/en/i18n/',
        )
        self.assertRedirects(
            self.client.get('/i18n/', HTTP_ACCEPT_LANGUAGE='de'),
            '/de/i18n/',
        )

        self.assertContains(
            self.client.get('/en/i18n/'),
            'en',
        )
        self.assertContains(
            self.client.get('/de/i18n/'),
            'de',
        )

    def test_render_plugins(self):
        """Test both render_plugins and render_plugin"""

        page = Page.objects.create(
            is_active=True,
            title='main',
            slug='main',
            template_key='with-sidebar',
        )
        page.testapp_richtext_set.create(
            ordering=0,
            region='main',
            text='<b>main</b>',
        )
        page.testapp_richtext_set.create(
            ordering=0,
            region='sidebar',
            text='<i>sidebar</b>',
        )

        response = self.client.get(page.get_absolute_url())
        self.assertContains(
            response,
            '<div class="main"><b>main</b></div>',
        )
        self.assertContains(
            response,
            '<div class="sidebar"><i>sidebar</b></div>',
        )

    def test_add_duplicated_path(self):
        """Non-unique paths should also be detected upon direct addition"""

        Page.objects.create(
            title='main',
            slug='main',
        )

        client = self.login()
        response = client.post('/admin/testapp/page/add/', merge_dicts(
            {
                'title': 'main',
                'slug': 'main',
                'language_code': 'en',
                'application': '',
                'template_key': 'standard',
            },
            zero_management_form_data('testapp_richtext_set'),
            zero_management_form_data('testapp_image_set'),
            zero_management_form_data('testapp_snippet_set'),
            zero_management_form_data('testapp_external_set'),
            zero_management_form_data('testapp_html_set'),
        ))
        self.assertContains(
            response,
            'Page with this Path already exists.',
            status_code=200,
        )

    def test_non_empty_static_paths(self):
        """Static paths may not be left empty"""
        client = self.login()
        response = client.post('/admin/testapp/page/add/', merge_dicts(
            {
                'title': 'main',
                'slug': 'main',
                'language_code': 'en',
                'application': '',
                'template_key': 'standard',
                'static_path': True,
                'path': '',
            },
            zero_management_form_data('testapp_richtext_set'),
            zero_management_form_data('testapp_image_set'),
            zero_management_form_data('testapp_snippet_set'),
            zero_management_form_data('testapp_external_set'),
            zero_management_form_data('testapp_html_set'),
        ))
        self.assertContains(
            response,
            'Static paths cannot be empty. Did you mean',
            status_code=200,
        )

    def test_reverse(self):
        """Test all code paths through reverse_fallback and reverse_any"""

        self.assertEqual(
            reverse_fallback('test', reverse, 'not-exists'),
            'test',
        )
        self.assertEqual(
            reverse_fallback('test', reverse, 'admin:index'),
            '/admin/',
        )
        self.assertEqual(
            reverse_any((
                'not-exists',
                'admin:index',
            )),
            '/admin/',
        )
        with six.assertRaisesRegex(
                self,
                NoReverseMatch,
                "Reverse for any of 'not-exists-1', 'not-exists-2' with"
                " arguments '\[\]' and keyword arguments '{}' not found."
        ):
            reverse_any(('not-exists-1', 'not-exists-2'))

    def test_move_clean_and_save(self):
        """Test that a page move does the right thing (model state should be
        restored after clean() so that save() updates the MPTT attributes
        for real, without a ROLLBACK"""

        client = self.login()

        r1 = Page.objects.create(
            title='root 1',
            slug='root-1',
        )
        r2 = Page.objects.create(
            title='root 2',
            slug='root-2',
        )
        child = Page.objects.create(
            parent_id=r1.id,
            title='child',
            slug='child',
        )

        ContentType.objects.clear_cache()  # because of 13. below

        with self.assertNumQueries(15):
            # NOTE NOTE NOTE!
            # The exact count is not actually important. What IS important is
            # that the query count does not change without us having a chance
            # to inspect.
            #
            #  1. session
            #  2. AppsMiddleware / apps_urlconf
            #  3. request.user
            #  4. SAVEPOINT
            #  5. fetch child
            #  6. fetch root-2
            #  7. exists() new parent (root-2)
            #  8. fetch descendants (why?)
            #  9. path uniqueness check of descendants with (/root-2/child/)
            # 10. path uniqueness of self
            # 11. page.save()
            # 12. fetch descendants for looping
            # 13. get page Django content type
            # 14. insert into admin log
            # 15. RELEASE SAVEPOINT
            response = client.post(
                reverse('admin:testapp_page_change', args=(child.id,)),
                merge_dicts(
                    {
                        'title': 'child',
                        'slug': 'child',
                        'path': '/root-1/child/',
                        'static_path': '',
                        'language_code': 'en',
                        'application': '',
                        'is_active': 1,
                        'menu': 'main',
                        'template_key': 'standard',
                        'parent': r2.id,
                    },
                    zero_management_form_data('testapp_richtext_set'),
                    zero_management_form_data('testapp_image_set'),
                    zero_management_form_data('testapp_snippet_set'),
                    zero_management_form_data('testapp_external_set'),
                    zero_management_form_data('testapp_html_set'),
                ),
            )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            [(
                page.pk,
                page.parent_id,
                page.position,
            ) for page in Page.objects.all()],
            [
                (r1.pk, None, 10),
                (r2.pk, None, 20),
                (child.pk, r2.pk, 10),
            ]
        )

    def prepare_for_move(self):
        root = Page.objects.create(
            title='root',
            slug='root',
        )
        p1 = Page.objects.create(
            title='p1',
            slug='p1',
            parent=root,
        )
        p2 = Page.objects.create(
            title='p2',
            slug='p2',
            parent=root,
        )

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p1.pk, root.pk, 10),
                (p2.pk, root.pk, 20),
            ])

        return root, p1, p2

    def test_move_to_root_last(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        response = client.get(
            reverse('admin:testapp_page_move', args=(p1.pk,)),
        )
        self.assertContains(response, '*** p1', 1)
        self.assertContains(response, '--- p2', 1)

        response = client.post(
            reverse('admin:testapp_page_move', args=(p1.pk,)),
            {
                'move_to': 'last',
                'of': '',
            })

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p2.pk, root.pk, 20),
                (p1.pk, None, 20),
            ])

    def test_move_to_root_first(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        client.post(
            reverse('admin:testapp_page_move', args=(p2.pk,)),
            {
                'move_to': 'first',
                'of': '',
            })

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (p2.pk, None, 10),
                (root.pk, None, 20),
                (p1.pk, root.pk, 10),
            ])

    def test_move_to_child(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        client.post(
            reverse('admin:testapp_page_move', args=(p2.pk,)),
            {
                'move_to': 'first',
                'of': p1.pk,
            })

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p1.pk, root.pk, 10),
                (p2.pk, p1.pk, 10),
            ])

    def test_invalid_move(self):
        root, p1, p2 = self.prepare_for_move()
        client = self.login()

        response = client.post(
            reverse('admin:testapp_page_move', args=(root.pk,)),
            {
                'move_to': 'first',
                'of': p1.pk,
            })

        self.assertContains(
            response,
            'Select a valid choice. That choice is not one of the available choices.',  # noqa
        )

    def test_reorder_siblings(self):
        root, p1, p2 = self.prepare_for_move()

        p3 = Page.objects.create(
            title='p3',
            slug='p3',
            parent=root,
        )
        client = self.login()

        client.post(
            reverse('admin:testapp_page_move', args=(p3.pk,)),
            {
                'move_to': 'right',
                'of': p1.pk,
            })

        self.assertEqual(
            [(p.pk, p.parent_id, p.position) for p in Page.objects.all()],
            [
                (root.pk, None, 10),
                (p1.pk, root.pk, 10),
                (p3.pk, root.pk, 20),
                (p2.pk, root.pk, 30),
            ])

    def test_redirects(self):
        page1 = Page.objects.create(
            title='home',
            slug='home',
            path='/de/',
            static_path=True,
            language_code='de',
            is_active=True,
        )
        page2 = Page.objects.create(
            title='something',
            slug='something',
            path='/something/',
            static_path=True,
            language_code='de',
            is_active=True,
            redirect_to_page=page1,
        )
        page3 = Page.objects.create(
            title='something2',
            slug='something2',
            path='/something2/',
            static_path=True,
            language_code='de',
            is_active=True,
            redirect_to_url='http://example.com/',
        )

        self.assertRedirects(
            self.client.get(page2.get_absolute_url()),
            page1.get_absolute_url(),
        )

        self.assertRedirects(
            self.client.get(page3.get_absolute_url(), follow=False),
            'http://example.com/',
            fetch_redirect_response=False,
        )

        # Everything fine in clean-land
        self.assertIs(page2.clean(), None)

        # Both redirects cannot be set at the same time
        self.assertRaises(
           ValidationError,
           lambda: Page(
                title='test',
                slug='test',
                language_code='de',
                redirect_to_page=page1,
                redirect_to_url='nonempty',
            ).full_clean(),
        )

        # No chain redirects
        self.assertRaises(
           ValidationError,
           lambda: Page(
                title='test',
                slug='test',
                language_code='de',
                redirect_to_page=page2,
            ).full_clean(),
        )

        # No redirects to self
        page2.redirect_to_page = page2
        self.assertRaises(ValidationError, page2.full_clean)

    def test_positional(self):
        @positional(2)
        def test(a, b, c):
            pass

        with self.assertRaises(TypeError):
            test(1, 2, 3)

        test(1, 2, c=3)

    def test_subclasses(self):
        class A(object):
            pass

        class B(A):
            pass

        class C(B):
            pass

        self.assertEqual(
            set(iterate_subclasses(A)),
            {B, C},
        )

        class Test(models.Model):
            class Meta:
                abstract = True

        class Test2(Test):
            class Meta:
                abstract = True

        self.assertEqual(
            concrete_model(Test),
            None,
        )

    def test_standalone_renderer(self):
        """The renderer also works when used without a wrapping template"""

        renderer = TemplatePluginRenderer()
        renderer.register_template_renderer(
            HTML,
            'renderer/html.html',
        )

        page = Page.objects.create(
            template_key='standard',
        )
        HTML.objects.create(
            parent=page,
            ordering=10,
            region='main',
            html='<b>Hello</b>',
        )

        regions = renderer.regions(page)
        self.assertEqual(
            regions.render('main', Context()),
            '<b>Hello</b>\n',
        )
