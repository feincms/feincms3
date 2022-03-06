Cookie control
==============

Some jurisidictions require the the users' consent before adding analytics
scripts and tracking cookies. While it may be best to not use any analytics and
tracking at all this may not be possible or even desirable in all
circumstances.

Many solutions exist for adding a consent banner to the website. Some of those
banners require loading JavaScript and other assets from external servers. This
raises some questions because loading those scripts may also be seen as
tracking already. It is certainly safer to implement a cookie control panel
locally. It would be boring to start from scratch on each site.

This guide explains how to use `feincms3-cookiecontrol <https://github.com/feinheit/feincms3-cookiecontrol/>`__.

Installation
~~~~~~~~~~~~

Install the package:

.. code-block:: shell

    venv/bin/pip install feincms3-cookiecontrol

Add ``feincms3_cookiecontrol`` to ``INSTALLED_APPS`` and add a custom location
for the migrations to ``MIGRATION_MODULES``. (feincms3-cookiecontrol cannot
bundle migrations because it builds on `django-translated-fields
<https://github.com/matthiask/django-translated-fields>`__ which has to know
the list of available languages to create migrations.)

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "feincms3_cookiecontrol",
    ]

    MIGRATION_MODULES = {
        "feincms3_cookiecontrol": "app.migrate.feincms3_cookiecontrol",
    }

.. note::
   You are of course free to use other values for ``MIGRATION_MODULES``. The
   example above just works well. You'll have to create the ``migrate`` folder
   yourself and place an empty ``__init__.py`` file in there. Read the Django
   documentation for additional guidance.

Create and apply the initial migration:

.. code-block:: shell

    python manage.py makemigrations feincms3_cookiecontrol
    python manage.py migrate

Optionally load the fixture; it contains two cookie categories (essential and
analytics) with short descriptions and translations (english, german, french
and italian) while ignoring translations which aren't in use on your site:

.. code-block:: shell

    python manage.py loaddata --ignorenonexistent f3cc-categories

Add the panel to the template, e.g. in ``base.html`` at the end of the
``<body>`` element:

.. code-block:: html+django

    <!doctype html>
    <html>
      ...
      <body>
        ...
        {% load feincms3_cookiecontrol %}{% feincms3_cookiecontrol %}
      </body>
    </html>

You'll have to add all tracking scripts yourself now.


Customization
~~~~~~~~~~~~~

The default colors of the control panel may not fit into your site. The best
way to customize the appearance is to set a few CSS variables, e.g.:

.. code-block:: css

    #f3cc {
      --f3cc-accent-color: #abc;
    }


Hiding the button
~~~~~~~~~~~~~~~~~

The default presentation of the panel is a fixed banner at the bottom of the
viewport. Once any cookies have been accepted (essential cookies have to be
accepted, e.g. the CSRF cookie) the banner is replaced by a single button which
allows showing the control panel again.

You may want to suppress the button on some pages, for example on all pages
except for the privacy policy.

A good way to achieve this follows.

Let's assume you're using page types as described in
:ref:`templates-and-regions`. Let's also assume that your privacy policy page
uses the standard page type described in the guide:

.. code-block:: python

    class Page(AbstractPage, PageTypeMixin):
        TYPES = [
            TemplateType(
                key="standard",
                title=_("standard"),
                template_name="pages/standard.html",
                regions=[
                    Region(key="main", title=_("Main")),
                ],
            ),
        ]

We will add an additional page type which can be used as a marker. Since we're
using feincms3 apps be sure to read the :ref:`apps-introduction` if you haven't
done this already.

.. code-block:: python

    class Page(AbstractPage, PageTypeMixin):
        TYPES = [
            TemplateType(
                key="standard",
                title=_("standard"),
                template_name="pages/standard.html",
                regions=[
                    Region(key="main", title=_("Main")),
                ],
            ),
            ApplicationType(
                key="privacy-policy",
                title=_("privacy policy"),
                urlconf="feincms3.root.passthru",
                template_name="pages/standard.html",
                regions=[
                    Region(key="main", title=_("Main")),
                ],
            ),
        ]

.. note::
   We cannot just use a new ``TemplateType`` because we **only** want to hide
   the button on all other pages if a privacy policy page actually exists!

Now you can extend the ``page_context`` helper:

.. code-block:: python

    from feincms3.root.passthru import reverse_passthru

    def hide_modify_button(page):
        return bool(
            # We got a page instance
            page
            # The current page is not the privacy-policy page
            and page.type.key != "privacy-policy"
            # An active privacy policy page exists
            and reverse_passthru("privacy-policy", fallback=None)
        )

    def page_context(request, *, page=None):
        ...
        return {
            ...
            "hide_modify_button": hide_modify_button(page),
        }

It's a bit involved but it's good to write defensive code.

Now you can use this additional variable in the template:

.. code-block:: html+django

    <!doctype html>
    <html>
      ...
      <body>
        ...
        {% load feincms3_cookiecontrol %}
        {% feincms3_cookiecontrol hide_modify_button=hide_modify_button %}
      </body>
    </html>
