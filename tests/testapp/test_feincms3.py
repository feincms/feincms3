from __future__ import unicode_literals

import warnings

from django.contrib.auth.models import User
from django.contrib.messages.storage.cookie import CookieStorage
from django.db import IntegrityError, transaction
from django.forms.models import modelform_factory
from django.test import Client, TestCase
from django.utils.deprecation import RemovedInDjango20Warning
from django.utils.translation import deactivate_all, override

from feincms3.apps import (
    NoReverseMatch, apps_urlconf, reverse, reverse_any, reverse_fallback
)
from feincms3.plugins.external import ExternalForm

from .models import Page, External, Article


# I know that field.rel and rel.to have been deprecated, thank you.
warnings.filterwarnings(
    'ignore',
    category=RemovedInDjango20Warning,
    module=r'mptt')
# Something about inspect.getargspec in beautifulsoup4.
warnings.filterwarnings(
    'ignore',
    module=r'bs4\.builder\._lxml')


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


class Test(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            'admin', 'admin@test.ch', 'blabla')
        deactivate_all()

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
            '/static/mptt/draggable-admin.js',
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
        self.assertNotContains(
            response,
            '/static/mptt/draggable-admin.js',
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
                {
                    'testapp_richtext_set-0-text': '<span style="font-weight:bold">Hello!</span>',  # noqa
                    'testapp_richtext_set-TOTAL_FORMS': 1,
                    'testapp_richtext_set-0-region': 'main',
                    'testapp_richtext_set-0-ordering': 10,
                },
                {
                    'testapp_external_set-TOTAL_FORMS': 1,
                    'testapp_external_set-0-region': 'main',
                    'testapp_external_set-0-ordering': 10,
                    'testapp_external_set-0-url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # noqa
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
        self.assertContains(
            response,
            'src="https://www.youtube.com/embed/dQw4w9WgXcQ?feature=oembed"',
            1,
        )
        self.assertContains(
            response,
            'noembed-youtube',
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

    def test_navigation(self):
        """Test menu template tags"""

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
        sub.refresh_from_db()  # mptt bookkeeping

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
            ),
        )

        self.assertContains(
            response,
            'Database constraints are violated:'
            # ' UNIQUE constraint failed: testapp_page.path'
        )

    def test_duplicated_path_changelist(self):
        """The change list should not crash but handle the constraint error"""

        client = self.login()
        home, sub = self.duplicated_path_setup()

        response = client.post('/admin/testapp/page/', {
            'cmd': 'move_node',
            'position': 'last-child',
            'cut_item': sub.pk,
            'pasted_on': home.pk,
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        messages = CookieStorage(response)._decode(
            response.cookies['messages'].value,
        )

        self.assertEqual(len(messages), 1)
        self.assertTrue(('%s' % messages[0]).startswith(
            'Database error:'))

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
        ))
        self.assertContains(
            response,
            'Page with this Path already exists.',
            status_code=200,
        )

    def test_reverse(self):
        """Test all code paths through reverse_fallback and reverse_any"""

        self.assertEqual(
            reverse_fallback('test', 'not-exists'),
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
        with self.assertRaises(NoReverseMatch):
            reverse_any(('not-exists-1', 'not-exists-2'))
