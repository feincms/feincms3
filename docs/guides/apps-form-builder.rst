.. _apps-form-builder:

Adding a form builder app
=========================

The following example app uses `form_designer
<https://pypi.org/project/form_designer>`__ to provide a forms builder
integrated with the pages app described above. Apart from installing
form_designer itself the following steps are necessary.

Add an entry to ``Page.APPLICATIONS`` for the forms app:

.. code-block:: python

    from feincms3.apps import AppsMixin
    from feincms3.mixins inmport LanguageMixin
    from feincms3.pages import AbstractPage

    class Page(AppsMixin, LanguageMixin, ..., AbstractPage):
        # ...
        APPLICATIONS = [
            ("forms", _("forms"), {
                # Required: A module containing urlpatterns
                "urlconf": "app.forms",
                # The "form" field on the page is required when
                # selecting the forms app
                "required_fields": ("form",),
                # Not necessary, but helpful for finding a form's URL using
                # reverse_app("forms-{}".format(form.pk), "form")
                "app_instance_namespace": lambda page: "{}-{}".format(
                    page.application,
                    page.form_id,
                ),
            }),
            # ...
        ]
        form = models.ForeignKey(
            "form_designer.Form",
            on_delete=models.SET_NULL,
            blank=True, null=True,
            verbose_name=_("form"),
        )

Add the ``app/forms.py`` module itself. Note that since control is
directly handed to the application view and no page view code runs
you'll have to load the page instance yourself and do the necessary
language setup and provide the page etc. to the rendering context. The
best way to load the page instance responsible for the current app is by
calling :func:`feincms3.apps.page_for_app_request`:

.. code-block:: python

    from django.conf.urls import url
    from django.http import HttpResponseRedirect
    from django.shortcuts import render

    from feincms3.apps import page_for_app_request

    from app.pages.renderer import renderer


    def form(request):
        page = page_for_app_request(request)
        page.activate_language(request)

        context = {}

        if "ok" not in request.GET:
            form_class = page.form.form()

            if request.method == "POST":
                form = form_class(request.POST)

                if form.is_valid():
                    # Discard return values from form processing.
                    page.form.process(form, request)
                    return HttpResponseRedirect("?ok")

            else:
                form = form_class()

            context["form"] = form

        context.update({
            "page": page,
            "regions": renderer.regions(
                page, inherit_from=page.ancestors().reverse()),
        })

        return render(request, "form.html", context)


    app_name = "forms"
    urlpatterns = [
        url(r"^$", form, name="form"),
    ]

Add the required template:

.. code-block:: html

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
