"""
Uses the `Noembed <https://noembed.com/>`_ oEmbed service to embed (almost)
arbitrary URLs. Depends on `requests <https://docs.python-requests.org>`_.
"""

from hashlib import md5

from django import forms
from django.core.cache import cache
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _

import requests
from content_editor.admin import ContentEditorInline


__all__ = (
    "External",
    "ExternalInline",
    "oembed_json",
    "oembed_html",
    "render_external",
)


def oembed_json(url, *, cache_failures=True):
    """
    Asks `Noembed <https://noembed.com/>`_ for the embedding HTML code for
    arbitrary URLs. Sites supported include Youtube, Vimeo, Twitter and many
    others.

    Successful embeds are always cached for 30 days.

    Failures are cached if ``cache_failures`` is ``True`` (the default). The
    durations are as follows:

    - Connection errors are cached 60 seconds with the hope that the connection
      failure is only transient.
    - HTTP errors codes and responses in an unexpected format (no JSON) are
      cached for 24 hours.

    The return value is always a dictionary, but it may be empty.
    """
    # Thundering herd problem etc...
    key = "oembed-url-%s-data" % md5(url.encode("utf-8")).hexdigest()
    data = cache.get(key)
    if data is not None:
        return data

    try:
        data = requests.get(
            "https://noembed.com/embed",
            params={"url": url, "nowrap": "on", "maxwidth": 1200, "maxheight": 800},
            timeout=2,
        ).json()
    except (requests.ConnectionError, requests.ReadTimeout):
        # Connection failed? Hopefully temporary, try again soon.
        timeout = 60
    except (ValueError, requests.HTTPError):
        # Oof... HTTP error code, or no JSON? Try again tomorrow,
        # and we should really log this.
        timeout = 86400
    else:
        # Perfect, cache for 30 days
        cache.set(key, data, timeout=30 * 86400)
        return data

    if cache_failures:
        cache.set(key, {}, timeout=timeout)
    return {}


def oembed_html(url, *, cache_failures=True):
    """
    Wraps :func:`~feincms3.plugins.external.oembed_json`, but only returns
    the HTML part of the OEmbed response.

    The return value is always either a HTML fragment or an empty string.
    """
    return oembed_json(url, cache_failures=cache_failures).get("html", "")


def render_external(plugin, **kwargs):
    """
    Render the plugin, embedding it in the appropriate markup for Foundation's
    responsive-embed element
    (https://foundation.zurb.com/sites/docs/responsive-embed.html)
    """

    html = oembed_html(plugin.url)
    if "youtube.com" in html:
        html = '<div class="responsive-embed widescreen">%s</div>' % (html,)
    elif "vimeo.com" in html:
        html = '<div class="responsive-embed widescreen vimeo">%s</div>' % (html,)
    return mark_safe(html)


class External(models.Model):
    """
    External content plugin
    """

    url = models.URLField(_("URL"))

    class Meta:
        abstract = True
        verbose_name = _("external content")

    def __str__(self):
        return self.url


class ExternalForm(forms.ModelForm):
    """
    Tries fetching the oEmbed code for the given URL when cleaning form data
    """

    def clean(self):
        data = super(ExternalForm, self).clean()
        url = data.get("url")
        if url and not oembed_html(url, cache_failures=False):
            raise forms.ValidationError(
                ugettext("Unable to fetch HTML for this URL, sorry!")
            )
        return data


class ExternalInline(ContentEditorInline):
    """
    Content editor inline using the ``ExternalForm`` to verify whether the
    given URL is embeddable using oEmbed or not.
    """

    form = ExternalForm
