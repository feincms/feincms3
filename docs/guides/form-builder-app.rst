.. _form-builder-app:

Adding a form builder app
=========================

The following example app uses `form_designer
<https://pypi.org/project/form_designer>` to provide a forms builder
integrated with the pages app described above. Apart from installing
form_designer itself the following steps are necessary.

Add an entry to ``Page.APPLICATIONS`` for the forms app. The
``app_instance_namespace`` bit is not strictly necessary, but it might
be helpful to reverse URLs where a specific form is integrated using
``reverse_app(('forms-%s' % form.pk,), 'form')``:

.. code-block:: python

    from feincms3.apps import AppsMixin
    from feincms3.mixins inmport LanguageMixin
    from feincms3.pages import AbstractPage

    class Page(AppsMixin, LanguageMixin, ..., AbstractPage):
        # ...
        APPLICATIONS = [
            ("forms", _("forms"), {
                "urlconf": "app.forms",
                "app_instance_namespace": lambda page: "%s-%s" % (
                    page.application,
                    page.form_id,
                ),
                "required_fields": ("form",),
            }),
            # ...
        ]
        form = models.ForeignKey(
            "form_designer.Form",
            on_delete=models.SET_NULL,
            blank=True, null=True,
            verbose_name=_("form"),
        )

Add the ``app/forms.py`` module itself:

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
