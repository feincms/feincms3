from django.apps import AppConfig
from django.core import checks
from django.utils.translation import gettext_lazy as _


MIDDLEWARE = "feincms3.redirects.middleware.redirects_middleware"


class RedirectsConfig(AppConfig):
    name = "feincms3.redirects"
    # The default label "redirects" would clash too easily.
    label = "feincms3_redirects"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("redirects")

    def ready(self):
        checks.register(check_middleware)


def check_middleware(app_configs, **kwargs):
    from django.conf import settings  # noqa: PLC0415

    if MIDDLEWARE in settings.MIDDLEWARE:
        return []
    return [
        checks.Error(
            f'"{MIDDLEWARE}" must be in MIDDLEWARE when "feincms3.redirects" is'
            " installed.",
            hint=(
                "Add it before the page middleware. Silence this check if you"
                " call feincms3.redirects.middleware.redirect_response yourself."
            ),
            id="feincms3.E008",
        )
    ]
