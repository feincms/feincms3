from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from feincms3.redirects import _registry
from feincms3.redirects.models import Redirect


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "target",
        "is_automatic",
        "permanent",
        "created_at",
    ]
    list_filter = ["is_automatic", "permanent", "content_type"]
    search_fields = ["host", "path", "target_url"]
    readonly_fields = ["is_automatic", "created_at"]
    fieldsets = [
        (None, {"fields": ["host", "path", "permanent"]}),
        (
            _("Target"),
            {
                "fields": ["target_url", "content_type", "object_id"],
                "description": _(
                    "Either enter an URL or select an object. Redirects to"
                    " objects follow them when their URL changes."
                ),
            },
        ),
        (None, {"fields": ["is_automatic", "created_at"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("target_object")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "content_type":
            kwargs["queryset"] = ContentType.objects.filter(
                pk__in=[
                    ContentType.objects.get_for_model(model).pk for model in _registry
                ]
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=_("target"))
    def target(self, obj):
        if not (url := obj.get_target_url()):
            return _("(does not exist)")
        if obj.target_url:
            return url
        return format_html("{} ({})", obj.target_object, url)

    def save_model(self, request, obj, form, change):
        # Redirects edited by hand aren't automatic anymore.
        obj.is_automatic = False
        super().save_model(request, obj, form, change)
