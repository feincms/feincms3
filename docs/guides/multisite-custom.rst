Multisite Custom Site Model
===========================

Since feincms3-sites 0.13.1 you can use a custom site model instead
of the default provided ``feincms3_sites.Site``.

Configuration
~~~~~~~~~~~~~

First, make sure that you adjust your Django settings accordingly:

.. code-block:: python

    # FEINCMS3_SITES_SITE_MODEL = "feincms3_sites.Site"
    FEINCMS3_SITES_SITE_MODEL = "myapp.Site"

From now on, Django will use your custom site model.


Implementing a Custom Site Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, you have to implement your custom site model, by adding the following
to your models, e.g.:

.. code-block:: python

    from feincms3_sites.models import AbstractSite
    from feincms3_meta.models import MetaMixin

    class CustomSite(AbstractSite, MetaMixin):
        name = models.CharField(max_length=100, blank=False, null=False)

        def __str__(self):
            return "{} ({})".format(self.name, self.host)

The above will add the additional ``name`` field to the site that is also
used for display in dropdowns and lists in the site admin, e.g.
``MySite (localhost:8000)``.

It will also inherit meta fields declared by the ``MetaMixin`` that can be
used for providing default meta information to the pages associated with that
site. (you will have to install feincms3-meta and enable the app in
your Django settings to use it.)

Please note that the metadata from the site will not be added automatically,
you will have to do this in your view, e.g.

.. code-block:: python

    from django.shortcuts import get_object_or_404, render, redirect

    from feincms3.regions import Regions
    from feincms3_meta.utils import meta_tags

    from .models import Page
    from .renderer import renderer


    def page_detail(request, path=None):
        """
        The view expects uri paths to be formed as such

        [[/<language-code>][/<path>]]

        in case of an empty uri path the view will redirect the user to

        /<site.default_language/

        expecting a root page to exist that has the appropriate path

        otherwise, the provided uri path will be used and the system will
        try to retrieve a probably existing page via the ORM.
        """
        actual_site = request.site
        if not path:
            # make sure that the user is redirected to the correct url
            # we expect a root page with custom path /<default_language>/ to exist here
            redirect_path = "/{}/".format(actual_site.default_language)
            return redirect(redirect_path)

        actual_path = "/{}/".format(path)
        page = get_object_or_404(
            Page.objects.active(),
            path=actual_path
        )
        page.activate_language(request)
        ancestors = page.ancestors().reverse()
        meta_data_providers = [page] + list(ancestors) + [page.site]
        return render(
            request,
            page.type.template_name,
            {
                "page": page,
                "regions": Regions.from_item(
                    page,
                    renderer=renderer,
                    inherit_from=ancestors,
                    timeout=60
                ),
                "meta_tags": meta_tags(
                    meta_data_providers,
                    request=request,
                    # The default site model doesn't have a name attribute, see the custom site model above
                    site_name=page.site.name
                )
            },
        )

Make sure that your custom site model gets registered with the Django ORM
before your page model gets registered, otherwise there will be an exception
telling you that the site model configured in ``FEINCMS3_SITES_SITE_MODEL``
does not exist.

Remember to update your migrations as well:

.. code-block:: shell

    ./manage.py makemigrations
    ./manage.py migrate


Implementing a Custom Site Model Admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from django.contrib import admin
    from django.utils.translation import gettext_lazy as _

    from feincms3_sites.admin import DefaultLanguageListFilter
    from feincms3_sites.admin import SiteAdmin
    from feincms3_meta.models import MetaMixin

    from .models import Site


    @admin.register(Site)
    class CustomSiteAdmin(SiteAdmin):
        list_display = [
            "name", "host", "default_language", "is_active", "is_default"
        ]

        list_filter = [
            "is_active", "host", "name", DefaultLanguageListFilter
        ]

        fieldsets = [
            (None, {
                "fields": [
                    "name",
                    "host",
                    "default_language",
                    "is_active",
                    "is_default",
                ],
            }),
            (_("Advanced Settings"), {
                "fields": [
                    "is_managed_re",
                    "host_re",
                ],
                "classes": [
                    "tabbed"
                ],
            }),
            MetaMixin.admin_fieldset()
        ]

By default, the admin edit/create page will display itself as a flat admin page,
i.e. there will not be any tabs.

In comes the ``django-content-editor`` and the scripts and other media it provides.

So to have tabs on your custom site model's admin page, add the following to
the ``SiteAdmin``:

.. code-block:: python

    ...

    class CustomSiteAdmin(SiteAdmin):

        ...

        class Media:
            css = {
                "all": [
                    "content_editor/material-icons.css",
                    "content_editor/content_editor.css",
                ]
            }
            js = [
                "admin/js/jquery.init.js",
                "content_editor/tabbed_fieldsets.js",
            ]
