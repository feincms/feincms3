"""
Redirects for URLs which do not exist (anymore)

Add ``"feincms3.redirects"`` to ``INSTALLED_APPS`` and register the models
whose URLs should be remembered:

.. code-block:: python

    from feincms3 import redirects

    redirects.register(Page, queryset=lambda request: Page.objects.active())
    redirects.register(Article)

Each time an instance of a registered model is saved its current URL (the
return value of ``get_absolute_url()``) is recorded. When the URL changes
later, e.g. because a page has been moved or its slug has been changed, the
old URL still points to the instance and requests are redirected to its new
URL. This also works if an URL changes without the instance being saved, e.g.
when the page an app is attached to is moved, as long as the instance has been
saved once before (or recorded using the ``record_redirects`` management
command) at its old URL.

The redirects are applied to responses with a status code of 404 by
:func:`feincms3.redirects.middleware.redirects_middleware`.
"""

from dataclasses import dataclass
from typing import Any

from django.db.models.signals import post_save


__all__ = ["register", "registration"]


@dataclass(frozen=True)
class Registration:
    model: Any
    queryset: Any
    get_host: Any
    select_related: tuple = ()

    def get_queryset(self, request):
        """
        Return the queryset of instances which may be redirected to
        """
        if self.queryset is None:
            qs = self.model._default_manager.all()
        elif callable(self.queryset):
            qs = self.queryset(request)
        else:
            qs = self.queryset.all()
        return qs.select_related(*self.select_related)

    def get_all_queryset(self):
        """
        Return a queryset of all instances, e.g. for showing them in the admin
        """
        return self.model._base_manager.select_related(*self.select_related)


_registry = {}


def register(model, *, queryset=None, get_host=None, select_related=()):
    """
    Register a model for automatically recording its URLs

    Optional arguments:

    - ``queryset``: The queryset of instances which may be redirected to, or a
      callable accepting the request and returning a queryset. Use this to
      avoid redirecting to inactive pages or to instances of a different
      site. Defaults to all instances.
    - ``get_host``: A callable accepting an instance and returning the host
      the instance's URLs belong to, or an empty string if they are valid for
      all hosts. Defaults to the host of the URL returned by
      ``get_absolute_url()``, which is empty for URLs without a domain.
      Projects with several sites should pass e.g. ``lambda page:
      page.site.host``.
    - ``select_related``: Relations which ``get_absolute_url()`` uses, e.g.
      ``["page"]`` if the URL of the instance is built from the URL of a page.
      Avoids one query per instance when looking up redirects and listing
      them in the admin.

    Returns the model, so it can also be used as a class decorator.
    """
    model = model._meta.concrete_model
    _registry[model] = Registration(
        model=model,
        queryset=queryset,
        get_host=get_host,
        select_related=tuple(select_related),
    )
    post_save.connect(
        _post_save,
        sender=model,
        weak=False,
        dispatch_uid=f"feincms3.redirects:{model._meta.label}",
    )
    return model


def registration(model):
    """
    Return the registration of the model, or ``None``
    """
    return _registry.get(model._meta.concrete_model)


def _post_save(sender, instance, *, raw=False, **kwargs):
    if not raw:
        # Importing models here allows calling register() from models.py
        from feincms3.redirects.models import Redirect  # noqa: PLC0415

        Redirect.objects.record(instance)
