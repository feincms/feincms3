from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RedirectsConfig(AppConfig):
    name = "feincms3.redirects"
    # The default label "redirects" would clash too easily.
    label = "feincms3_redirects"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("redirects")
