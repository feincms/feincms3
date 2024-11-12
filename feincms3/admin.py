import json
from collections import defaultdict
from functools import update_wrapper

from django import forms
from django.contrib import messages
from django.contrib.admin import ModelAdmin, SimpleListFilter, display, helpers
from django.contrib.admin.options import IncorrectLookupParameters, csrf_protect_m
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import router, transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, re_path, reverse
from django.utils.html import format_html, mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from js_asset.js import JS
from tree_queries.forms import TreeNodeChoiceField


__all__ = (
    "TreeAdmin",
    "MoveForm",
    "CloneForm",
    "AncestorFilter",
    "action_form_view_decorator",
)


def action_form_view_decorator(modeladmin):
    def wrap(view):
        def wrapper(request, object_id):
            with transaction.atomic(using=router.db_for_write(modeladmin.model)):
                model = modeladmin.model
                opts = model._meta

                obj = modeladmin.get_object(request, unquote(object_id))

                if not modeladmin.has_change_permission(request, obj):
                    raise PermissionDenied

                if obj is None:
                    return modeladmin._get_obj_does_not_exist_redirect(
                        request, opts, object_id
                    )

                return modeladmin.admin_site.admin_view(view)(request, obj)

        wrapper.model_admin = modeladmin
        return csrf_protect(update_wrapper(wrapper, view))

    return wrap


class TreeAdmin(ModelAdmin):
    """
    ``ModelAdmin`` subclass for managing models using `django-tree-queries
    <https://github.com/matthiask/django-tree-queries>`_ trees.

    Shows the tree's hierarchy and adds a view to move nodes around. To use
    this class the three columns ``collapse_column``, ``indented_title`` and
    ``move_column`` should be added to subclasses ``list_display``::

        class NodeAdmin(TreeAdmin):
            list_display = [*TreeAdmin.list_display, ...]
            # This is the default:
            # list_display_links = ["indented_title"]

        admin.site.register(Node, NodeAdmin)
    """

    list_display = ["collapse_column", "indented_title", "move_column"]
    list_display_links = ["indented_title"]

    @csrf_protect_m
    def changelist_view(self, request, **kwargs):
        response = super().changelist_view(request, **kwargs)
        if not hasattr(response, "context_data"):
            return response
        context = self.tree_admin_context(request)
        response.context_data["media"] += forms.Media(
            css={"all": ["content_editor/material-icons.css", "feincms3/admin.css"]},
            js=[
                JS(
                    "feincms3/admin.js",
                    {"id": "feincms3-context", "data-context": json.dumps(context)},
                ),
            ],
        )
        return response

    def tree_admin_context(self, request):
        return {
            "initiallyCollapseDepth": 1,
        }

    def get_queryset(self, request):
        return self.model._default_manager.with_tree_fields()

    @display(description="")
    def collapse_column(self, instance):
        return format_html(
            '<div class="collapse-toggle collapse-hide" data-pk="{}" data-tree-depth="{}"></div>',
            instance.pk,
            instance.tree_depth,
        )

    def indented_title(self, instance, *, ellipsize=True):
        """
        Use Unicode box-drawing characters to visualize the tree hierarchy.
        """
        box_drawing = []
        for _i in range(instance.tree_depth - 1):
            box_drawing.append('<i class="l"></i>')
        if instance.tree_depth > 0:
            box_drawing.append('<i class="a"></i>')

        return format_html(
            '<div class="box">'
            '<div class="box-drawing">{}</div>'
            '<div class="box-text{}" style="text-indent:{}px">{}</div>'
            "</div>",
            mark_safe("".join(box_drawing)),
            " ellipsize" if ellipsize else "",
            instance.tree_depth * 30,
            instance,
        )

    indented_title.short_description = _("title")

    def move_column(self, instance):
        """
        Show a ``move`` link which leads to a separate page where the move
        destination may be selected.
        """
        return format_html(
            """\
<div class="move-controls">
<button class="move-cut" type="button" data-pk="{}" title="{}">
  <span class="material-icons">content_cut</span>
</button>
<select class="move-paste" data-pk="{}" title="{}">
  <option value="">---</option>
  <option value="before">{}</option> -->
  <option value="first-child">{}</option>
  <option value="last-child">{}</option>
  <option value="after">{}</option>
</select>
</div>
""",
            instance.pk,
            _("Move '{}' to a new location").format(instance),
            instance.pk,
            _("Choose new location"),
            _("before"),
            _("as first child"),
            _("as last child"),
            _("after"),
        )

        opts = self.model._meta
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                f"admin:{opts.app_label}_{opts.model_name}_move",
                args=(instance.pk,),
            ),
            _("move"),
        )

    move_column.short_description = _("move")

    def get_urls(self):
        """
        Add our own ``move`` view.
        """

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "move-node/",
                self.admin_site.admin_view(self.move_node_view),
            ),
            re_path(
                r"^(.+)/move/$",
                action_form_view_decorator(self)(self.move_view),
                name="{}_{}_move".format(*info),
            ),
            re_path(
                r"^(.+)/clone/$",
                action_form_view_decorator(self)(self.clone_view),
                name="{}_{}_clone".format(*info),
            ),
        ] + super().get_urls()

    def move_node_view(self, request):
        kw = {"request": request, "modeladmin": self}
        form = MoveNodeForm(request.POST, **kw)
        return HttpResponse(form.process())

    def move_view(self, request, obj):
        return self.action_form_view(
            request, obj, form_class=MoveForm, title=_("Move %s") % obj
        )

    def clone_view(self, request, obj):
        return self.action_form_view(
            request, obj, form_class=CloneForm, title=_("Clone %s") % obj
        )

    def action_form_view(self, request, obj, *, form_class, title):
        kw = {"request": request, "obj": obj, "modeladmin": self}
        form = form_class(request.POST if request.method == "POST" else None, **kw)
        if form.is_valid():
            return form.process()
        return self.render_action_form(request, form, title=title, obj=obj)

    def render_action_form(self, request, form, *, title, obj):
        adminform = helpers.AdminForm(
            form,
            [
                (None, {"fields": form.fields.keys()})
            ],  # list(self.get_fieldsets(request, obj)),
            {},  # self.get_prepopulated_fields(request, obj),
            (),  # self.get_readonly_fields(request, obj),
            model_admin=self,
        )
        media = self.media + adminform.media

        context = dict(
            self.admin_site.each_context(request),
            title=title,
            object_id=obj.pk,
            original=obj,
            adminform=adminform,
            errors=helpers.AdminErrorList(form, ()),
            preserved_filters=self.get_preserved_filters(request),
            media=media,
            is_popup=False,
            inline_admin_formsets=[],
            save_as_new=False,
            show_save_and_add_another=False,
            show_save_and_continue=False,
            show_delete=False,
        )

        response = self.render_change_form(
            request, context, add=False, change=True, obj=obj
        )

        # Suppress the rendering of the "save and add another" button.
        response.context_data["has_add_permission"] = False
        return response


class MoveNodeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.modeladmin = kwargs.pop("modeladmin")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        self.fields["move"] = forms.ModelChoiceField(
            queryset=self.modeladmin.get_queryset(self.request)
        )
        self.fields["relative_to"] = forms.ModelChoiceField(
            queryset=self.modeladmin.get_queryset(self.request)
        )
        positions = ("before", "first-child", "last-child", "after")
        self.fields["position"] = forms.ChoiceField(choices=zip(positions, positions))

    def process(self):
        if not self.is_valid():
            messages.error(self.request, _("Invalid node move request."))
            messages.error(self.request, str(self.errors))
            return "error"

        move = self.cleaned_data["move"]
        relative_to = self.cleaned_data["relative_to"]
        position = self.cleaned_data["position"]

        if position in {"first-child", "last-child"}:
            move._set_parent(relative_to)
            siblings_qs = relative_to.children
        else:
            move._set_parent(relative_to.parent)
            siblings_qs = relative_to.__class__._default_manager.filter(
                parent=relative_to.parent
            )

        try:
            # All fields of model are not in this form
            move.full_clean(exclude=[f.name for f in move._meta.get_fields()])
        except ValidationError as exc:
            messages.error(
                self.request,
                _("Error while validating the new position of '{}'.").format(move),
            )
            messages.error(self.request, str(exc))
            return "error"

        if position == "before":
            siblings_qs.filter(position__gte=relative_to.position).update(
                position=F("position") + 10
            )
            move.position = relative_to.position
            move.save()

        elif position == "after":
            siblings_qs.filter(position__gt=relative_to.position).update(
                position=F("position") + 10
            )
            move.position = relative_to.position + 10
            move.save()

        elif position == "first-child":
            siblings_qs.update(position=F("position") + 10)
            move.position = 10
            move.save()

        elif position == "last-child":
            move.position = 0  # Let AbstractPage.save handle the position
            move.save()

        else:  # pragma: no cover
            pass

        messages.success(
            self.request,
            _("Node '{}' has been moved to its new position.").format(move),
        )
        return "ok"


class MoveForm(forms.Form):
    """
    Allows making the node the left or right sibling or the first or last
    child of another node.

    Requires the node to be moved as ``obj`` keyword argument.
    """

    class Media:
        css = {"screen": ["feincms3/move-form.css"]}

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("obj")
        self.modeladmin = kwargs.pop("modeladmin")
        self.request = kwargs.pop("request")
        self.model = self.instance.__class__

        super().__init__(*args, **kwargs)

        choices = self._generate_choices(
            self.modeladmin.get_queryset(self.request).with_tree_fields()
        )
        self.fields["new_location"] = forms.ChoiceField(
            label=_("New location"),
            widget=forms.RadioSelect,
            choices=choices,
        )
        if len(choices) <= 1:
            messages.warning(
                self.request,
                _(
                    "Moving isn't possible because there are no valid targets."
                    " Maybe you selected the only root node?"
                ),
            )

    def _generate_choices(self, queryset):
        children = defaultdict(list)
        for node in queryset:
            children[node.parent_id].append(node)

        def _text_indent(depth):
            return mark_safe(f' style="text-indent:{depth * 30}px"')

        choices = []

        def _iterate(parent_id):
            for index, node in enumerate(children[parent_id]):
                if node == self.instance:
                    choice = (
                        "",
                        format_html(
                            '<div class="mv is-self"{}><strong>{}</strong>',
                            _text_indent(node.tree_depth),
                            node,
                        ),
                    )
                    if index == 0 and parent_id:
                        # Moving the first child of parent_id; do not remove parent_id
                        choices[-1] = (
                            choices[-1][0],
                            mark_safe(choices[-1][1].replace("mv-mark", "hidden")),
                        )
                        choices.append(choice)
                    else:
                        choices[-1] = choice
                    continue

                choices.append(
                    (
                        f"{node.id}:first",
                        format_html(
                            '<div class="mv to-first"{}><strong>{}</strong>'
                            '<div class="mv-mark"{}>&rarr; {}</div></div>',
                            _text_indent(node.tree_depth),
                            node,
                            _text_indent(node.tree_depth + 1),
                            _("move here"),
                        ),
                    )
                )
                _iterate(node.id)
                choices.append(
                    (
                        f"{node.id}:right",
                        format_html(
                            '<div class="mv to-right mv-mark"{}>&rarr; {}</div>',
                            _text_indent(node.tree_depth),
                            _("move here"),
                        ),
                    )
                )

        choices.append(
            (
                "0:first",
                format_html(
                    '<div class="mv to-root mv-mark">&rarr; {}</div>',
                    _("move here"),
                ),
            )
        )
        _iterate(None)
        return choices

    def clean(self):
        data = super().clean()
        if not data.get("new_location"):
            return data

        pk, _sep, first_or_right = data["new_location"].partition(":")
        data["first_or_right"] = first_or_right

        if pk == "0":
            self.instance.parent = None
            data["relative"] = None
        else:
            data["relative"] = self.instance.__class__._base_manager.get(pk=pk)

            if first_or_right == "first":
                self.instance.parent = data["relative"]
            else:
                self.instance.parent = data["relative"].parent

        # FIXME feincms3-sites would also require site_id,
        # feincms3-language-sites would also require language_code to be set
        # for the cleaning step to work correctly in all cases.

        # All fields of model are not in this form
        self.instance.full_clean(
            exclude=[f.name for f in self.model._meta.get_fields()]
        )

        return data

    def process(self):
        siblings = list(
            self.model._default_manager.filter(parent=self.instance.parent).exclude(
                pk=self.instance.pk
            )
        )
        relative = self.cleaned_data["relative"]
        first_or_right = self.cleaned_data["first_or_right"]

        if relative is None or first_or_right == "first":
            siblings.insert(0, self.instance)
        else:
            siblings.insert(siblings.index(relative) + 1, self.instance)

        for index, instance in enumerate(siblings):
            if instance == self.instance:
                instance.position = (index + 1) * 10
                instance.save()
            else:
                self.model._default_manager.filter(pk=instance.pk).update(
                    position=(index + 1) * 10
                )

        self.modeladmin.message_user(
            self.request,
            _("The node %(node)s has been moved to the new position.")
            % {"node": self.instance},
        )

        opts = self.modeladmin.model._meta
        return redirect(f"admin:{opts.app_label}_{opts.model_name}_changelist")


class CloneForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("obj")
        self.modeladmin = kwargs.pop("modeladmin")
        self.request = kwargs.pop("request")

        super().__init__(*args, **kwargs)

        self.fields["target"] = self.instance._meta.get_field("parent").formfield(
            form_class=TreeNodeChoiceField,
            label=capfirst(_("target")),
            required=True,
            label_from_instance=lambda obj: "{}{}".format(
                "".join(["*** " if obj == self.instance else "--- "] * obj.tree_depth),
                obj,
            ),
        )
        self.fields["target"].widget.attrs.update({"size": 30, "style": "height:auto"})

        self.fields["_set_content"] = forms.BooleanField(
            label=_("Replace target's content"),
            required=False,
            help_text=_("Affects the following models: %s.")
            % (
                ", ".join(
                    "%s" % inline.model._meta.verbose_name_plural
                    for inline in self.modeladmin.inlines
                ),
            ),
        )

        for field in sorted(
            self.instance._meta.get_fields(), key=lambda field: field.name
        ):
            if field.auto_created or not field.editable:
                continue

            self.fields[f"set_{field.name}"] = forms.BooleanField(
                label=(
                    f"{capfirst(field.verbose_name)} ({field.name})"
                    if hasattr(field, "verbose_name")
                    else field.name
                ),
                required=False,
                help_text=_('Current: "%s"') % (getattr(self.instance, field.name),),
            )

    def clean(self):
        data = super().clean()
        target = data.get("target")
        if target is None:
            return data

        if target == self.instance:
            raise forms.ValidationError({"target": _("Cannot clone node to itself.")})

        for field in self.instance._meta.get_fields():
            if self.cleaned_data.get(f"set_{field.name}"):
                setattr(target, field.name, getattr(self.instance, field.name))

        # All fields of model are not in this form
        target.full_clean(exclude=[f.name for f in target._meta.get_fields()])

        return data

    def process(self):
        target = self.cleaned_data["target"]
        fields = []

        for field in self.instance._meta.get_fields():
            if self.cleaned_data.get(f"set_{field.name}"):
                setattr(target, field.name, getattr(self.instance, field.name))
                fields.append("{}".format(getattr(field, "verbose_name", field.name)))

        if fields:
            self.modeladmin.message_user(
                self.request,
                _("Updated fields of %(node)s: %(fields)s")
                % {"node": target, "fields": ", ".join(fields)},
            )

        if self.cleaned_data.get("_set_content"):
            from django.forms.models import _get_foreign_key  # Since 2009.

            for inline in self.modeladmin.inlines:
                fk = _get_foreign_key(
                    self.modeladmin.model, inline.model, inline.fk_name, can_fail=False
                )

                # Remove all existing instances
                inline.model._default_manager.filter(**{fk.name: target}).delete()

                for obj in inline.model._default_manager.filter(
                    **{fk.name: self.instance}
                ):
                    obj.pk = None
                    setattr(obj, fk.name, target)
                    obj.save(force_insert=True)

            self.modeladmin.message_user(
                self.request,
                _("Replaced the content of %(target)s with the contents of %(source)s.")
                % {"target": target, "source": self.instance},
            )

        target.save()

        opts = self.modeladmin.model._meta
        return redirect(f"admin:{opts.app_label}_{opts.model_name}_change", target.pk)


class AncestorFilter(SimpleListFilter):
    """
    Only show the subtree of an ancestor

    By default, the first two levels are shown in the ``list_filter`` sidebar.
    This can be changed by setting the ``max_depth`` class attribute to a
    different value.

    Usage::

        class NodeAdmin(TreeAdmin):
            list_display = ("indented_title", "move_column", ...)
            list_filter = ("is_active", AncestorFilter, ...)

        admin.site.register(Node, NodeAdmin)
    """

    title = _("subtree")
    parameter_name = "ancestor"
    max_depth = 1

    def indent(self, depth):
        return mark_safe("&#x251c;" * depth)

    def lookups(self, request, model_admin):
        return [
            (node.id, format_html("{} {}", self.indent(node.tree_depth), node))
            for node in model_admin.model._default_manager.with_tree_fields().extra(
                where=["tree_depth <= %s" % self.max_depth]
            )
        ]

    def queryset(self, request, queryset):
        if self.value():
            try:
                node = queryset.model._default_manager.get(pk=self.value())
            except (TypeError, ValueError, queryset.model.DoesNotExist) as exc:
                raise IncorrectLookupParameters() from exc
            return queryset.descendants(node, include_self=True)
        return queryset
