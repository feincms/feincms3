Build your CMS
==============

To build a CMS you need to write your URLconf and views, and add
settings to your Django project.

The `feincms3-example <https://github.com/matthiask/feincms3-example>`_
project shows how everything works together. An explanation of the
necessary parts follows here.


Settings
~~~~~~~~

There are quite a few settings involved:

You'll have to add at least the following apps to ``INSTALLED_APPS``:

- ``feincms3``
- ``content_editor``
- ``ckeditor`` if you want to use :mod:`feincms3.plugins.richtext`
- ``imagefield`` for :mod:`feincms3.plugins.image`
- ... and of course also the app where you put your concrete models such
  as the page model, named ``app.pages`` in this guide.

If you're using the rich text plugin it is strongly recommended to add a
``CKEDITOR_CONFIGS`` setting as documented in :mod:`feincms3.cleanse`.


Models
~~~~~~

The page model and a few plugins could be defined as follows::

    from __future__ import unicode_literals

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from content_editor.models import Region, Template, create_plugin_base

    from feincms3 import plugins
    from feincms3.apps import AppsMixin
    from feincms3.mixins import TemplateMixin, MenuMixin, LanguageMixin
    from feincms3.pages import AbstractPage


    class Page(
        AbstractPage,
        AppsMixin,      # For adding the articles app to pages through the CMS.
        TemplateMixin,  # Two page templates, one with only a main
                        # region and another with a sidebar as well.
        MenuMixin,      # We have a main and a footer navigation (meta).
        LanguageMixin,  # We're building a multilingual CMS. (Also,
                        # feincms3.apps depends on LanguageMixin
                        # currently.)
    ):

        # TemplateMixin
        TEMPLATES = [
            Template(
                key='standard',
                title=_('standard'),
                template_name='pages/standard.html',
                regions=(
                    Region(key='main', title=_('Main')),
                ),
            ),
        ]

        # MenuMixin
        MENUS = [
            ('main', _('main')),
            ('footer', _('footer')),
        ]

        # AppsMixin. We have two apps, one is for company PR, the other
        # for a more informal blog.
        #
        # NOTE! The app names (first element in the tuple) have to match the
        # article categories exactly for URL reversing and filtering articles by
        # app to work! (See app.articles.models.Article.CATEGORIES)
        APPLICATIONS = [
            ('publications', _('publications'), {
                'urlconf': 'app.articles.urls',
            }),
            ('blog', _('blog'), {
                'urlconf': 'app.articles.urls',
            }),
        ]


    PagePlugin = create_plugin_base(Page)


    class RichText(plugins.RichText, PagePlugin):
        pass


    class Image(plugins.Image, PagePlugin):
        caption = models.CharField(
            _('caption'),
            max_length=200,
            blank=True,
        )


Views and URLs
~~~~~~~~~~~~~~

You're completely free to define your own views and URLs. That being
said, the ``AbstractPage`` class already has a ``get_absolute_url``
implementation which expects something like this::

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
look as follows::

    from django.shortcuts import get_object_or_404, render

    from .models import Page
    from .renderer import renderer


    def page_detail(request, path=None):
        page = get_object_or_404(
            Page.objects.active(),
            path=('/%s/' % path) if path else '/',
        )
        page.activate_language(request)
        return render(request, page.template.template_name, {
            'page': page,
            'regions': renderer.regions(
                page,
                inherit_from=page.ancestors().reverse(),
            ),
        })

.. note::
   `FeinCMS <https://github.com/feincms/feincms>`_ provided request and
   response processors and several ways how plugins (in FeinCMS: content
   types) could hook into the request-response processing. This isn't
   necessary with feincms3 -- simply put the functionality into your own
   views code.

Here's an example how plugins could be rendered,
``app.pages.renderer``::

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

Of course if you'd rather let plugins use templates, do this::

    renderer.register_template_renderer(
        Image,
        'plugins/image.html',
    )

And the associated template::

    <figure><img src="{{ plugin.image.url }}" alt=""/></figure>

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

For completeness, here's an example how the ``app.pages.admin`` module
might look like::

    from django.contrib import admin

    from content_editor.admin import ContentEditor
    from feincms3.admin import TreeAdmin
    from feincms3 import plugins

    from app.pages import models


    class PageAdmin(ContentEditor, TreeAdmin):
        list_display = (
            'indented_title', 'move_column', 'is_active',
            'menu', 'template_key', 'language_code', 'application')
        list_per_page = 250
        prepopulated_fields = {'slug': ('title',)}
        raw_id_fields = ('parent',)

        # fieldsets = ... (Recommended! No example here though. Note
        # that the content editor not only allows collapsed, but also
        # tabbed fieldsets -- simply add 'tabbed' to the 'classes' key
        # the same way you'd add 'collapse'.

        inlines = [
            plugins.RichTextInline.create(
                models.RichText,
            ),
            plugins.ImageInline.create(
                models.Image,
            ),
        ]

        # class Media: ... (Add font-awesome from a CDN and nicely
        # looking buttons for plugins as is described in
        # django-content-editor's documentation -- search for
        # "plugin_buttons.js")


    admin.site.register(models.Page, PageAdmin)


An example forms builder app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example app uses `form_designer
<https://pypi.org/project/form_designer>` to provide a forms builder
integrated with the pages app described above. Apart from installing
form_designer itself the following steps are necessary.

Add an entry to ``Page.APPLICATIONS`` for the forms app. The
``app_instance_namespace`` bit is not strictly necessary, but it might
be helpful to reverse URLs where a specific form is integrated using
``reverse_app(('forms-%s' % form.pk,), 'form')``::

    # ...
    class Page(...):
        # ...
        APPLICATIONS = [
            ('forms', _('forms'), {
                'urlconf': 'app.forms',
                'app_instance_namespace': lambda page: '%s-%s' % (
                    page.application,
                    page.form_id,
                ),
                'required_fields': ('form',),
            }),
            # ...
        ]
        form = models.ForeignKey(
            'form_designer.Form',
            on_delete=models.SET_NULL,
            blank=True, null=True,
            verbose_name=_('form'),
        )

Add the ``app/forms.py`` module itself::

    from django.conf.urls import url
    from django.http import HttpResponseRedirect
    from django.shortcuts import render

    from feincms3.apps import page_for_app_request

    from app.pages.renderer import renderer


    def form(request):
        page = page_for_app_request(request)
        page.activate_language(request)
        context = {}

        if 'ok' not in request.GET:
            form_class = page.form.form()

            if request.method == 'POST':
                form = form_class(request.POST)

                if form.is_valid():
                    # Discard return values from form processing.
                    page.form.process(form, request)
                    return HttpResponseRedirect('?ok')

            else:
                form = form_class()

            context['form'] = form

        context.update({
            'page': page,
            'regions': renderer.regions(
                page, inherit_from=page.ancestors().reverse()),
        })

        return render(request, 'form.html', context)


    app_name = 'forms'
    urlpatterns = [
        url(r'^$', form, name='form'),
    ]

Add the required template::

    {% extends "base.html" %}

    {% load feincms3_renderer %}

    {% block content %}

    {% render_region regions 'main' timeout=15 %}

    {% if form %}
      <form method="post" action=".#form" id="form">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Submit</button>
      </form>
    {% else %}
      <h1>Thank you!</h1>
    {% endif %}
    {% endblock %}

Of course if you'd rather add another URL for the "thank you" page
you're free to add a second entry to the ``urlpatterns`` list and
redirect to this URL instead.
