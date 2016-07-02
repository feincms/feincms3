from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import Client, TestCase

from .models import Page


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
                    'testapp_richtext_set-TOTAL_FORMS': 1,
                    'testapp_richtext_set-0-text': '<span style="font-weight:bold">Hello!</span>',  # noqa
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

        # print(response, response.content.decode('utf-8'))
