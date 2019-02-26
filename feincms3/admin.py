from __future__ import unicode_literals

from functools import update_wrapper

from django import forms
from django.conf.urls import url
from django.contrib.admin import ModelAdmin, SimpleListFilter, helpers
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.utils.text import capfirst
from django.utils.translation import pgettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

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
    this class the two columns ``indented_title`` and ``move_column`` should be
    added to subclasses ``list_display``::

        class NodeAdmin(TreeAdmin):
            list_display = ('indented_title', 'move_column', ...)

        admin.site.register(Node, NodeAdmin)
    """

    list_display = ("indented_title", "move_column")

    class Media:
        css = {"all": ["feincms3/box-drawing.css"]}

    def get_queryset(self, request):
        return self.model._default_manager.with_tree_fields()

    def indented_title(self, instance):
        """
        Use Unicode box-drawing characters to visualize the tree hierarchy.
        """
        box_drawing = []
        for i in range(instance.tree_depth - 1):
            box_drawing.append('<i class="l"></i>')
        if instance.tree_depth > 0:
            box_drawing.append('<i class="a"></i>')

        return format_html(
            '<div class="box">'
            '<div class="box-drawing">{}</div>'
            '<div class="box-text" style="text-indent:{}px">{}</div>'
            "</div>",
            mark_safe("".join(box_drawing)),
            instance.tree_depth * 30,
            instance,
        )

    indented_title.short_description = _("title")

    def move_column(self, instance):
        """
        Show a ``move`` link which leads to a separate page where the move
        destination may be selected.
        """
        opts = self.model._meta
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                "admin:%s_%s_move" % (opts.app_label, opts.model_name),
                args=(instance.pk,),
            ),
            _("move"),
        )

    move_column.short_description = ""

    def get_urls(self):
        """
        Add our own ``move`` view.
        """

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(
                r"^(.+)/move/$",
                action_form_view_decorator(self)(self.move_view),
                name="%s_%s_move" % info,
            ),
            url(
                r"^(.+)/clone/$",
                action_form_view_decorator(self)(self.clone_view),
                name="%s_%s_clone" % info,
            ),
        ] + super(TreeAdmin, self).get_urls()

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
        adminForm = helpers.AdminForm(
            form,
            [
                (None, {"fields": form.fields.keys()})
            ],  # list(self.get_fieldsets(request, obj)),
            {},  # self.get_prepopulated_fields(request, obj),
            (),  # self.get_readonly_fields(request, obj),
            model_admin=self,
        )
        media = self.media + adminForm.media

        context = dict(
            self.admin_site.each_context(request),
            title=title,
            object_id=obj.pk,
            original=obj,
            adminform=adminForm,
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


class MoveForm(forms.Form):
    """
    Allows making the node the left or right sibling or the first or last
    child of another node.

    Requires the node to be moved as ``obj`` keyword argument.
    """

    MOVE_CHOICES = (
        ("left", _("left sibling")),
        ("right", _("right sibling")),
        ("first", _("first child")),
        ("last", _("last child")),
    )

    move_to = forms.ChoiceField(
        label=_("Make node"), choices=MOVE_CHOICES, widget=forms.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("obj")
        self.modeladmin = kwargs.pop("modeladmin")
        self.request = kwargs.pop("request")
        self.model = self.instance.__class__

        super(MoveForm, self).__init__(*args, **kwargs)

        queryset = self.model._default_manager.with_tree_fields()
        self.fields["of"] = TreeNodeChoiceField(
            label=pgettext("MoveForm", "Of"),
            required=False,
            queryset=queryset.exclude(pk__in=queryset.descendants(self.instance)),
            label_from_instance=lambda obj: "{}{}".format(
                "".join(["*** " if obj == self.instance else "--- "] * obj.tree_depth),
                obj,
            ),
        )
        self.fields["of"].widget.attrs.update({"size": 30, "style": "height:auto"})

    def clean(self):
        data = super(MoveForm, self).clean()
        if not data.get("move_to"):
            return data

        if data.get("of") and data.get("of") == self.instance:
            raise forms.ValidationError(
                {"of": _("Cannot move node to a position relative to itself.")}
            )

        if not data.get("of"):
            self.instance.parent = None
        elif data["move_to"] in ("left", "right"):
            self.instance.parent = data.get("of").parent
        else:
            self.instance.parent = data.get("of")

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
        of = self.cleaned_data["of"]
        move_to = self.cleaned_data["move_to"]

        if move_to == "first" or (not of and move_to == "left"):
            siblings.insert(0, self.instance)
        elif move_to == "last" or (not of and move_to == "right"):
            siblings.append(self.instance)
        elif move_to == "left":
            siblings.insert(siblings.index(of), self.instance)
        elif move_to == "right":
            siblings.insert(siblings.index(of) + 1, self.instance)

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
            _("The node %(node)s has been made the" " %(move_to)s of node %(to)s.")
            % {
                "node": self.instance,
                "move_to": dict(self.MOVE_CHOICES).get(
                    self.cleaned_data["move_to"], self.cleaned_data["move_to"]
                ),
                "to": self.cleaned_data["of"] or _("root node"),
            },
        )

        opts = self.modeladmin.model._meta
        return redirect("admin:%s_%s_changelist" % (opts.app_label, opts.model_name))


class CloneForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("obj")
        self.modeladmin = kwargs.pop("modeladmin")
        self.request = kwargs.pop("request")

        super(CloneForm, self).__init__(*args, **kwargs)

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

            self.fields["set_{}".format(field.name)] = forms.BooleanField(
                label=(
                    "{} ({})".format(capfirst(field.verbose_name), field.name)
                    if hasattr(field, "verbose_name")
                    else field.name
                ),
                required=False,
                help_text=_('Current: "%s"') % (getattr(self.instance, field.name),),
            )

    def clean(self):
        data = super(CloneForm, self).clean()
        target = data.get("target")
        if target is None:
            return data

        if target == self.instance:
            raise forms.ValidationError({"target": _("Cannot clone node to itself.")})

        for field in self.instance._meta.get_fields():
            if self.cleaned_data.get("set_{}".format(field.name)):
                setattr(target, field.name, getattr(self.instance, field.name))

        # All fields of model are not in this form
        target.full_clean(exclude=[f.name for f in target._meta.get_fields()])

        return data

    def process(self):
        target = self.cleaned_data["target"]
        fields = []

        for field in self.instance._meta.get_fields():
            if self.cleaned_data.get("set_{}".format(field.name)):
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
                    self.modeladmin.model, inline.model, inline.fk_name, False
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
        return redirect(
            "admin:%s_%s_change" % (opts.app_label, opts.model_name), target.pk
        )


class AncestorFilter(SimpleListFilter):
    """
    Only show the subtree of an ancestor

    By default, the first two levels are shown in the ``list_filter`` sidebar.
    This can be changed by setting the ``max_depth`` class attribute to a
    different value.

    Usage::

        class NodeAdmin(TreeAdmin):
            list_display = ('indented_title', 'move_column', ...)
            list_filter = ('is_active', AncestorFilter, ...)

        admin.site.register(Node, NodeAdmin)
    """

    title = _("ancestor")
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
            except (TypeError, ValueError, queryset.model.DoesNotExist):
                raise IncorrectLookupParameters()
            return queryset.descendants(node, include_self=True)
        return queryset
