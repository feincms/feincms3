from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.forms.models import modelform_factory
from django.test import Client, TestCase

from feincms3.plugins.external import ExternalForm

from .models import Page, External


def _messages(response):
    return [m.message for m in response.context['messages']]


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


class AdminTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            'admin', 'admin@test.ch', 'blabla')

    def login(self):
        client = Client()
        client.force_login(self.user)
        return client

    def test_modules(self):
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

        # print(response, response.content.decode('utf-8'))

    def test_external_form_validation(self):
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

        # print(self.client.get('/en/a-en/').content.decode('utf-8'))
        # print(self.client.get('/de/b-de/').content.decode('utf-8'))
