from collections import defaultdict

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from feincms3.redirects import _registry, registration
from feincms3.redirects.models import Redirect, _url


def load_targets(rows):
    """
    Load the target objects of redirects with one query per model, using the
    ``select_related`` of the registrations, and set ``row.target_instance``
    """
    ids = defaultdict(set)
    for row in rows:
        row.target_instance = None
        if row.content_type_id and row.object_id:
            ids[row.content_type_id].add(row.object_id)
    targets = {}
    for ct_id, object_ids in ids.items():
        model = ContentType.objects.get_for_id(ct_id).model_class()
        if model is None or not (reg := registration(model)):
            continue
        pk = model._meta.pk
        for obj in reg.get_all_queryset().filter(
            pk__in=[pk.to_python(object_id) for object_id in object_ids]
        ):
            targets[ct_id, str(obj.pk)] = obj
    for row in rows:
        row.target_instance = targets.get((row.content_type_id, row.object_id))


class RedirectChangeList(ChangeList):
    def get_results(self, request):
        super().get_results(request)
        load_targets(self.result_list)


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

    def get_changelist(self, request, **kwargs):
        return RedirectChangeList

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
        if obj.target_url:
            return obj.target_url
        if (target := obj.target_instance) is None or not (url := _url(target)):
            return _("(does not exist)")
        return format_html("{} ({})", target, url)

    def save_model(self, request, obj, form, change):
        # Redirects edited by hand aren't automatic anymore.
        obj.is_automatic = False
        super().save_model(request, obj, form, change)
