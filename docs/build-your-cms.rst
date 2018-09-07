.. _build-your-cms:

Build your CMS
==============

This guide shows step by step how to use the tools provided by feincms3
to build your own CMS.

.. note::
  If you just want to quickly check out what feincms3 is capable of,
  have a look at the `feincms3-example
  <https://github.com/matthiask/feincms3-example>`__ project. It shows
  how everything works together, but also uses advanced functionality
  which might be confusing to newcomers and is not necessary for smaller
  CMS projects.


Getting started
~~~~~~~~~~~~~~~

Install feincms3 and all recommended dependencies:

.. code-block:: shell

    pip install feincms3[all]

Add the following settings:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "feincms3",
        "content_editor",
         # Optional, but not for this guide:
        "ckeditor",
        "imagefield",
    ]


Configure the rich text editor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The bundled rich text plugin (which we're going to integrate) uses
:class:`feincms3.cleanse.CleansedRichTextField` which always sends HTML
through `html-sanitizer
<https://pypi.org/project/html-sanitizer>`_. The default
configuration of HTML sanitizer is really restrictive and removes images
(besides other things such as normalizing the HTML and removing script
tags etc.)

The corresponding django-ckeditor configuration follows. It should also
be added to your settings:

.. code-block:: python

    # Configure django-ckeditor
    CKEDITOR_CONFIGS = {
        "default": {
            "toolbar": "Custom",
            "format_tags": "h1;h2;h3;p;pre",
            "toolbar_Custom": [[
                "Format", "RemoveFormat", "-",
                "Bold", "Italic", "Subscript", "Superscript", "-",
                "NumberedList", "BulletedList", "-",
                "Anchor", "Link", "Unlink", "-",
                "HorizontalRule", "SpecialChar", "-",
                "Source",
            ]],
        },
    }
    CKEDITOR_CONFIGS["richtext-plugin"] = CKEDITOR_CONFIGS["default"]

.. note::
   HTML copy-pasted from other sources (e.g. Word) is often messy. It is
   generally a good idea to sanitize HTML on the server side to prevent
   XSS attacks or even just the general uglyness that results from
   giving website editors too much freedom.

   We almost never allow embedding images, tables etc. into rich text
   elements on our sites. It is just too easy to add a 10MB JPEG or even
   a BMP file and scale it down to 50x50. Adding images as a separate
   plugin has other benefits too: No parsing of rich texts to replace
   images, it's much easier to e.g. create a lightbox, use the first
   image on the site as teaser image or whatever comes to your mind.

   That being said, adding your own rich text plugin which allows
   whatever you want is quite straightforward and completely supported.


Models
~~~~~~

The page model and a few plugins could be defined as follows:

.. code-block:: python

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from content_editor.models import Region, create_plugin_base

    from feincms3 import plugins
    from feincms3.pages import AbstractPage


    class Page(AbstractPage):
        regions = [
            Region(key="main", title=_("Main")),
        ]


    PagePlugin = create_plugin_base(Page)


    class RichText(plugins.richtext.RichText, PagePlugin):
        pass


    class Image(plugins.image.Image, PagePlugin):
        caption = models.CharField(_('caption'), max_length=200, blank=True)


Views and URLs
~~~~~~~~~~~~~~

You're completely free to define your own views and URLs. That being
said, the ``AbstractPage`` class already has a ``get_absolute_url``
implementation which expects something like this:

.. code-block:: python

    from django.conf.urls import url

    from app.pages import views


    app_name = 'pages'
    urlpatterns = [
        url(r'^(?P<path>[-\w/]+)/$', views.page_detail, name='page'),
        url(r'^$', views.page_detail, name='root'),
    ]

If you don't like this, you're completely free to write your own views,
URLs and ``get_absolute_url`` method.

With the URLconf above the view in the ``app.pages.views`` module would
look as follows:

.. code-block:: python

    from django.shortcuts import get_object_or_404, render

    from .models import Page
    from .renderer import renderer


    def page_detail(request, path=None):
        page = get_object_or_404(
            Page.objects.active(),
            path='/{}/'.format(path) if path else '/',
        )
        return render(request, "pages/standard.html", {
            "page": page,
            "regions": renderer.regions(page),
        })

.. note::
   `FeinCMS <https://github.com/feincms/feincms>`_ provided request and
   response processors and several ways how plugins (in FeinCMS: content
   types) could hook into the request-response processing. This isn't
   necessary with feincms3 -- simply put the functionality into your own
   views code.

Rendering and templates
~~~~~~~~~~~~~~~~~~~~~~~

Here's an example how plugins could be rendered,
``app.pages.renderer``:

.. code-block:: python

    from django.utils.html import format_html, mark_safe

    from feincms3.renderer import TemplatePluginRenderer

    from .models import Page, RichText, Image


    renderer = TemplatePluginRenderer()
    renderer.register_string_renderer(
        RichText,
        lambda plugin: mark_safe(plugin.text),
    )
    renderer.register_string_renderer(
        Image,
        lambda plugin: format_html(
            '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
            plugin.image.url,
            plugin.caption,
        ),
    )

Of course if you'd rather let plugins use templates, do this:

.. code-block:: python

    renderer.register_template_renderer(
        Image,
        'plugins/image.html',
    )

And the associated template::

    <figure>
      <img src="{{ plugin.image.url }}" alt="{{ plugin.caption }}"/>
      {% if plugin.caption %}<figcaption>{{ plugin.caption }}</figcaption>{% endif %}
    </figure>

The default image field also offers built-in support for thumbnailing
and cropping with a PPOI (primary point of interest); have a look at the
`django-imagefield <https://django-imagefield.readthedocs.io>`_ docs to
find out how.

And a ``pages/standard.html`` template::

    {% extends "base.html" %}

    {% load feincms3_renderer %}

    {% block title %}{{ page.title }} - {{ block.super }}{% endblock %}

    {% block content %}
      <main>
        <h1>{{ page.title }}</h1>
        {% render_region regions "main" %}
        {# or maybe {% render_region regions "main" timeout=30 %} #}
      </main>
    {% endblock %}


Admin classes
~~~~~~~~~~~~~

Here's an example how the ``app.pages.admin`` module might look like:

.. code-block:: python

    from django.contrib import admin

    from content_editor.admin import ContentEditor
    from feincms3 import plugins
    from feincms3.admin import TreeAdmin

    from app.pages import models


    class PageAdmin(ContentEditor, TreeAdmin):
        list_display = ["indented_title", "move_column", "is_active"]
        prepopulated_fields = {"slug": ("title",)}
        raw_id_fields = ["parent"]

        inlines = [
            plugins.richtext.RichTextInline.create(models.RichText),
            plugins.image.ImageInline.create(models.Image),
        ]

        # fieldsets = ... (Recommended! No example here though. Note
        # that the content editor not only allows collapsed, but also
        # tabbed fieldsets -- simply add 'tabbed' to the 'classes' key
        # the same way you'd add 'collapse'.

        # class Media: ... (Add font-awesome from a CDN and nicely
        # looking buttons for plugins as is described in
        # django-content-editor's documentation -- search for
        # "plugin_buttons.js")


    admin.site.register(models.Page, PageAdmin)
