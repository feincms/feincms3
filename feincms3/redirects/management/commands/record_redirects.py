from django.core.management.base import BaseCommand

from feincms3.redirects import _registry
from feincms3.redirects.models import Redirect


class Command(BaseCommand):
    help = "Record the current URLs of all instances of registered models."

    def handle(self, **options):
        for model in _registry:
            count = 0
            for instance in model._default_manager.iterator():
                Redirect.objects.record(instance)
                count += 1
            self.stdout.write(f"{model._meta.label}: {count} instances")
