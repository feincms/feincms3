import io

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings
from django.utils.translation import override
from pytest_django.asserts import assertContains, assertNotContains

from feincms3 import redirects
from feincms3.applications import _del_apps_urlconf_cache, apps_urlconf
from feincms3.redirects.models import Redirect
from testapp.models import Article, Page
from testapp.utils import override_urlconf


def create_pages():
    home = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        page_type="standard",
    )
    about = Page.objects.create(
        title="about",
        slug="about",
        parent=home,
        language_code="en",
        page_type="standard",
    )
    team = Page.objects.create(
        title="team",
        slug="team",
        parent=about,
        language_code="en",
        page_type="standard",
    )
    return home, about, team


@pytest.mark.django_db
def test_moved_pages_redirect(client):
    _home, about, _team = create_pages()
    assert client.get("/en/about/team/").status_code == 200

    about.slug = "about-us"
    about.save()

    # The page and its descendants have been recorded at both URLs
    assert set(Redirect.objects.values_list("path", flat=True)) == {
        "/en/",
        "/en/about/",
        "/en/about/team/",
        "/en/about-us/",
        "/en/about-us/team/",
    }

    response = client.get("/en/about/team/")
    assert response.status_code == 301
    assert response["Location"] == "/en/about-us/team/"

    # The query string is kept
    response = client.get("/en/about/?a=1")
    assert response["Location"] == "/en/about-us/?a=1"

    # APPEND_SLASH
    response = client.get("/en/about")
    assert response["Location"] == "/en/about-us/"

    # Existing pages are served normally
    assert client.get("/en/about-us/team/").status_code == 200

    # Moving back removes the redirect by making the row point to the
    # current URL again
    about.slug = "about"
    about.save()
    assert client.get("/en/about/team/").status_code == 200
    response = client.get("/en/about-us/team/")
    assert response["Location"] == "/en/about/team/"


@pytest.mark.django_db
def test_inactive_and_deleted_targets(client):
    _home, _about, team = create_pages()
    team.slug = "people"
    team.save()
    assert client.get("/en/about/team/").status_code == 301

    # Inactive pages aren't contained in the registered queryset
    team.is_active = False
    team.save()
    assert client.get("/en/about/team/").status_code == 404

    # Rows of deleted objects are kept but do not resolve
    team.delete()
    assert Redirect.objects.filter(path="/en/about/team/").exists()
    assert client.get("/en/about/team/").status_code == 404


@pytest.mark.django_db
def test_new_object_takes_over_path(client):
    _home, about, team = create_pages()
    team.slug = "people"
    team.save()

    other = Page.objects.create(
        title="team",
        slug="team",
        parent=about,
        language_code="en",
        page_type="standard",
    )
    row = Redirect.objects.get(path="/en/about/team/")
    assert row.object_id == str(other.pk)
    assert client.get("/en/about/team/").status_code == 200


@pytest.mark.django_db
def test_moved_app_redirects_articles(client):
    home = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        page_type="standard",
    )
    blog = Page.objects.create(
        title="blog",
        slug="blog",
        parent=home,
        language_code="en",
        page_type="blog",
    )

    with override_urlconf(apps_urlconf()), override("en"):
        article = Article.objects.create(title="Article", category="blog")
    _del_apps_urlconf_cache()
    assert Redirect.objects.filter(path=f"/en/blog/{article.pk}/").exists()

    # Articles aren't saved when the app page moves
    blog.slug = "news"
    blog.save()

    response = client.get(f"/en/blog/{article.pk}/")
    assert response.status_code == 301
    assert response["Location"] == f"/en/news/{article.pk}/"
    assert client.get(response["Location"]).status_code == 200


@pytest.mark.django_db
def test_unresolvable_urls_are_skipped():
    # No app page exists, get_absolute_url() raises NoReverseMatch
    Article.objects.create(title="Article", category="blog")
    assert not Redirect.objects.exists()


@pytest.mark.django_db
def test_manual_redirects_and_hosts(client):
    Redirect.objects.create(path="/old/", target_url="/new/", permanent=False)
    Redirect.objects.create(path="/index.php?id=12", target_url="/twelve/")
    Redirect.objects.create(host="example.com", path="/old/", target_url="/ex/")

    response = client.get("/old/")
    assert response.status_code == 302
    assert response["Location"] == "/new/"

    response = client.get("/old/?x=1")
    assert response["Location"] == "/new/?x=1"

    with override_settings(ALLOWED_HOSTS=["example.com", "testserver"]):
        response = client.get("/old/", headers={"host": "example.com:8000"})
    assert response["Location"] == "/ex/"

    response = client.get("/index.php?id=12")
    assert response.status_code == 301
    assert response["Location"] == "/twelve/"

    # Other query strings aren't matched
    assert client.get("/index.php?id=13").status_code == 404


@pytest.mark.django_db
def test_redirect_to_object_of_other_model(client):
    home = Page.objects.create(
        title="home",
        slug="home",
        path="/en/",
        static_path=True,
        language_code="en",
        page_type="standard",
    )
    Page.objects.create(
        title="blog",
        slug="blog",
        parent=home,
        language_code="en",
        page_type="blog",
    )
    article = Article.objects.create(title="Article", category="blog")
    Redirect.objects.create(
        path="/en/old-page/",
        content_type=ContentType.objects.get_for_model(Article),
        object_id=str(article.pk),
    )
    response = client.get("/en/old-page/")
    assert response["Location"] == f"/en/blog/{article.pk}/"


@pytest.mark.django_db
def test_validation():
    with pytest.raises(ValidationError):
        Redirect(path="old/", target_url="/new/").full_clean()
    with pytest.raises(ValidationError):
        Redirect(path="/old/").full_clean()


@pytest.mark.django_db
def test_record_redirects_command():
    home, _about, _team = create_pages()
    Page.objects.create(
        title="blog",
        slug="blog",
        parent=home,
        language_code="en",
        page_type="blog",
    )
    article = Article.objects.create(title="Article", category="blog")
    Redirect.objects.all().delete()

    stdout = io.StringIO()
    call_command("record_redirects", stdout=stdout)
    _del_apps_urlconf_cache()

    # Apps' URLs are available in the management command, too
    assert set(Redirect.objects.values_list("path", flat=True)) == {
        "/en/",
        "/en/about/",
        "/en/about/team/",
        "/en/blog/",
        f"/en/blog/{article.pk}/",
    }
    assert "testapp.Page: Recorded 4 of 4 URLs" in stdout.getvalue()
    assert "testapp.Article: Recorded 1 of 1 URLs" in stdout.getvalue()


@pytest.mark.django_db
def test_errors_do_not_prevent_saving(monkeypatch, caplog):
    def get_absolute_url(self):
        raise AttributeError("broken")

    monkeypatch.setattr(Article, "get_absolute_url", get_absolute_url)
    article = Article.objects.create(title="Article", category="blog")
    assert article.pk
    assert not Redirect.objects.exists()
    assert "Could not record the URL of testapp.Article" in caplog.text


@pytest.mark.django_db
def test_path_normalization():
    row = Redirect(path="/caf%C3%A9/?q=%C3%A9", target_url="/new/")
    row.full_clean()
    assert row.path == "/café/?q=%C3%A9"


@pytest.mark.django_db
def test_target_validation():
    _home, _about, team = create_pages()
    page_type = ContentType.objects.get_for_model(Page)

    Redirect(path="/old/", content_type=page_type, object_id=str(team.pk)).full_clean()

    with pytest.raises(ValidationError) as exc:
        Redirect(path="/old/", content_type=page_type, object_id="0").full_clean()
    assert "object_id" in exc.value.message_dict

    with pytest.raises(ValidationError) as exc:
        Redirect(
            path="/old/",
            content_type=ContentType.objects.get_for_model(Redirect),
            object_id="1",
        ).full_clean()
    assert "content_type" in exc.value.message_dict

    with pytest.raises(ValidationError) as exc:
        Redirect(
            path="/old/",
            target_url="/new/",
            content_type=page_type,
            object_id=str(team.pk),
        ).full_clean()
    assert "target_url" in exc.value.message_dict


@pytest.mark.django_db
def test_admin(admin_client):
    _home, about, team = create_pages()
    team.slug = "people"
    team.save()
    Redirect.objects.create(path="/manual/", target_url="https://example.com/")

    response = admin_client.get("/admin/feincms3_redirects/redirect/")
    assertContains(response, "/en/about/people/")
    assertContains(response, "https://example.com/")

    # Only registered models can be selected
    response = admin_client.get("/admin/feincms3_redirects/redirect/add/")
    page_type = ContentType.objects.get_for_model(Page)
    assertContains(response, f'<option value="{page_type.pk}">')
    assertNotContains(
        response,
        f'<option value="{ContentType.objects.get_for_model(Redirect).pk}">',
    )

    # Editing an automatic redirect makes it a manual redirect
    row = Redirect.objects.get(path="/en/about/team/")
    assert row.is_automatic
    response = admin_client.post(
        f"/admin/feincms3_redirects/redirect/{row.pk}/change/",
        {
            "host": "",
            "path": "/en/about/team/",
            "permanent": "on",
            "target_url": "",
            "content_type": page_type.pk,
            "object_id": str(about.pk),
        },
    )
    assert response.status_code == 302
    row.refresh_from_db()
    assert not row.is_automatic
    assert row.object_id == str(about.pk)


def test_middleware_check():
    from feincms3.redirects.apps import check_middleware  # noqa: PLC0415

    assert check_middleware(None) == []
    with override_settings(MIDDLEWARE=[]):
        assert [e.id for e in check_middleware(None)] == ["feincms3.E008"]


@pytest.mark.django_db
def test_admin_loads_targets_in_bulk(admin_client, monkeypatch):
    # Like a manual's chapter whose URL is built from its page's URL
    def get_absolute_url(self):
        prefix = self.parent.path if self.parent else "/"
        return f"{prefix}{self.slug}/"

    monkeypatch.setattr(Page, "get_absolute_url", get_absolute_url)
    monkeypatch.setitem(redirects._registry, Page, redirects.registration(Page))
    redirects.register(Page, queryset=Page.objects.active(), select_related=["parent"])

    _home, about, _team = create_pages()
    Redirect.objects.create(path="/manual/", target_url="https://example.com/")

    def count_queries():
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/admin/feincms3_redirects/redirect/")
        return response, len(ctx.captured_queries)

    _response, few = count_queries()
    for i in range(10):
        Page.objects.create(
            title=f"page {i}",
            slug=f"page-{i}",
            parent=about,
            language_code="en",
            page_type="standard",
        )
    response, many = count_queries()
    assertContains(response, "/en/about/page-9/")
    # Ten additional targets do not need additional queries
    assert few == many
