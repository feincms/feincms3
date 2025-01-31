import pytest
from pytest_django.asserts import assertContains

from testapp.models import Page


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
