from django.core.management.base import BaseCommand
from django.urls import set_urlconf

from feincms3 import applications
from feincms3.redirects import _registry
from feincms3.redirects.models import Redirect


class Command(BaseCommand):
    help = "Record the current URLs of all instances of registered models."

    def handle(self, **options):
        # The URLs of apps are only available in requests (through
        # apps_middleware) unless we add them ourselves.
        if applications._APPS_MODEL is not None:
            set_urlconf(applications.apps_urlconf())
        try:
            for model, reg in _registry.items():
                total = recorded = 0
                for instance in reg.get_all_queryset().iterator():
                    total += 1
                    recorded += Redirect.objects.record(instance)
                self.stdout.write(
                    f"{model._meta.label}: Recorded {recorded} of {total} URLs"
                )
        finally:
            set_urlconf(None)
