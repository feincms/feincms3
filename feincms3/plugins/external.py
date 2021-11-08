"""
Uses the `Noembed <https://noembed.com/>`_ oEmbed service to embed (almost)
arbitrary URLs. Depends on `requests <https://docs.python-requests.org>`_.
"""

import json
from hashlib import md5

import requests
from content_editor.admin import ContentEditorInline
from django import forms
from django.core.cache import cache
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import gettext, gettext_lazy as _


__all__ = (
    "External",
    "ExternalInline",
    "NoembedValidationForm",
    "oembed_json",
    "oembed_html",
    "render_external",
)


def oembed_json(url, *, cache_failures=True, force_refresh=False, params=None):
    """
    Asks `Noembed <https://noembed.com/>`_ for the embedding HTML code for
    arbitrary URLs. Sites supported include YouTube, Vimeo, Twitter and many
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
    p = {"url": url, "nowrap": "on", "maxwidth": 1200, "maxheight": 800}
    if params:
        p.update(params)
    key = (
        "oembed-url-%s-data"
        % md5(json.dumps(p, sort_keys=True).encode("utf-8")).hexdigest()
    )

    data = None if force_refresh else cache.get(key)
    if data is not None:
        return data

    try:
        data = requests.get("https://noembed.com/embed", params=p, timeout=2).json()
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


def oembed_html(url, **kwargs):
    """
    Wraps :func:`~feincms3.plugins.external.oembed_json`, but only returns
    the HTML part of the OEmbed response.

    The return value is always either a HTML fragment or an empty string.
    """
    return oembed_json(url, **kwargs).get("html", "")


def render_external(plugin, **kwargs):
    """
    Render the plugin, embedding it in the appropriate markup for `Foundation's
    responsive-embed element
    <https://foundation.zurb.com/sites/docs/responsive-embed.html>`__

    The HTML embed code is generated using
    :func:`~feincms3.plugins.external.oembed_html`. Maybe you want to take a
    look at :mod:`feincms3.embedding` for a less versatile but much faster
    alternative.
    """

    html = oembed_html(plugin.url)
    if "youtube.com" in html:
        html = f'<div class="responsive-embed widescreen youtube">{html}</div>'
    elif "vimeo.com" in html:
        html = f'<div class="responsive-embed widescreen vimeo">{html}</div>'
    return mark_safe(html)


class External(models.Model):
    """
    External content plugin
    """

    url = models.URLField(_("URL"))
    alternative_text = models.CharField(
        _("alternative text"),
        help_text=_("Describe the contents, e.g. for screenreaders."),
        max_length=1000,
        blank=True,
    )
    caption = models.CharField(_("caption"), blank=True, max_length=1000)

    class Meta:
        abstract = True
        verbose_name = _("external content")

    def __str__(self):
        return self.caption or self.url


class NoembedValidationForm(forms.ModelForm):
    """
    Tries fetching the oEmbed code for the given URL when cleaning form data

    This isn't active by default. If you want to validate URLs you should use
    the following snippet:

    .. code-block:: python

        from app.pages import models
        from feincms3 import plugins

        class SomeAdmin(...):
            inlines = [
                ...
                plugins.external.ExternalInline.create(
                    model=models.External,
                    form=plugins.external.NoembedValidationForm,
                ),
                ...
            ]
    """

    def clean(self):
        data = super().clean()
        url = data.get("url")
        if url and not oembed_html(url, cache_failures=False):
            raise forms.ValidationError(
                gettext("Unable to fetch HTML for this URL, sorry!")
            )
        return data


class ExternalInline(ContentEditorInline):
    button = '<span class="material-icons">movie_creation</span>'
