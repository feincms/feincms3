from functools import update_wrapper

from django import forms
from django.conf.urls import url
from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _, pgettext
try:
    from django.urls import reverse
except ImportError:  # pragma: no cover
    # Django <1.10
    from django.core.urlresolvers import reverse


csrf_protect_m = method_decorator(csrf_protect)


class TreeAdmin(ModelAdmin):
    """
    ``ModelAdmin`` subclass for managing models using django-cte-forest_
    trees.

    Shows the tree's hierarchy and adds a view to move nodes around. To use
    this class the two columns ``indented_title`` and ``move_column`` should be
    added to subclasses ``list_display``::

        class PageAdmin(TreeAdmin):  # Maybe also ContentEditor for pages.
            list_display = ('indented_title', 'move_column', ...)

        admin.site.register(Page, PageAdmin)
    """

    list_display = ('indented_title', 'move_column')

    class Media:
        css = {'all': {
            'feincms3/box-drawing.css',
        }}

    def get_ordering(self, request):
        """
        Order by tree (depth-first traversal) and ``position`` within a level
        """
        return (self.model._cte_node_ordering, 'position')

    def indented_title(self, instance):
        """
        Use Unicode box-drawing characters to visualize the tree hierarchy.
        """
        box_drawing = []
        for i in range(instance.depth - 2):
            box_drawing.append('<span>&#x2502;</span>')
        if instance.depth > 1:
            box_drawing.append('<span>&#x251c;</span>')

        return format_html(
            '<div class="box">'
            '<div class="box-drawing">{}</div>'
            '<div class="box-text" style="text-indent:{}px">{}</div>'
            '</div>',
            mark_safe(''.join(box_drawing)),
            (instance.depth - 1) * 40,
            instance,
        )
    indented_title.short_description = _('title')

    def move_column(self, instance):
        """
        Show a ``move`` link which leads to a separate page where the move
        destination may be selected.
        """
        opts = self.model._meta
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                'admin:%s_%s_move' % (opts.app_label, opts.model_name),
                args=(instance.pk,),
            ),
            _('move'),
        )
    move_column.short_description = ''

    def get_urls(self):
        """
        Add our own ``move`` view.
        """
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            url(r'^(.+)/move/$', wrap(self.move_view),
                name='%s_%s_move' % info),
        ] + super(TreeAdmin, self).get_urls()

    @csrf_protect_m
    def move_view(self, request, object_id):
        with transaction.atomic(using=router.db_for_write(self.model)):
            model = self.model
            opts = model._meta

            obj = self.get_object(request, unquote(object_id))

            if not self.has_change_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404()

            if request.method == 'POST':
                form = MoveForm(request.POST, obj=obj)

                if form.is_valid():
                    form.save()
                    self.message_user(request, _(
                        'The node %(node)s has been made the'
                        ' %(move_to)s of node %(to)s.'
                    ) % {
                        'node': obj,
                        'move_to': dict(MoveForm.MOVE_CHOICES).get(
                            form.cleaned_data['move_to'],
                            form.cleaned_data['move_to']),
                        'to': form.cleaned_data['of'] or _('root node'),
                    })

                    return redirect('admin:%s_%s_changelist' % (
                        opts.app_label, opts.model_name))

            else:
                form = MoveForm(obj=obj)

            adminForm = helpers.AdminForm(
                form,
                [(None, {
                    'fields': ('move_to', 'of'),
                })],  # list(self.get_fieldsets(request, obj)),
                {},  # self.get_prepopulated_fields(request, obj),
                (),  # self.get_readonly_fields(request, obj),
                model_admin=self)
            media = self.media + adminForm.media

            context = dict(
                self.admin_site.each_context(request),
                title=_('Move %s') % obj,
                object_id=object_id,
                original=obj,
                adminform=adminForm,
                errors=helpers.AdminErrorList(form, ()),
                preserved_filters=self.get_preserved_filters(request),
                media=media,
                is_popup=False,

                save_as_new=False,
                show_save_and_add_another=False,
                show_save_and_continue=False,
                show_delete=False,
            )

            return self.render_change_form(
                request, context, add=False, change=False, obj=obj)


class MoveForm(forms.Form):
    """
    Allows making the node the left or right sibling or the first or last
    child of another node.

    Requires the node to be moved as ``obj`` keyword argument.
    """
    MOVE_CHOICES = (
        ('left', _('left sibling')),
        ('right', _('right sibling')),
        ('first', _('first child')),
        ('last', _('last child')),
    )

    move_to = forms.ChoiceField(
        label=_('Make node'),
        choices=MOVE_CHOICES,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('obj')
        self.model = self.instance.__class__

        super(MoveForm, self).__init__(*args, **kwargs)

        self.fields['of'] = forms.ModelChoiceField(
            label=pgettext('MoveForm', 'Of'),
            required=False,
            queryset=self.model.objects.exclude(
                pk__in=self.instance.descendants(),
            ),
            widget=forms.Select(attrs={'size': 30, 'style': 'height:auto'}),
        )

        self.fields['of'].choices = [
            (None, '----------'),
        ] + [
            (
                obj.pk,
                '%s%s' % (
                    (obj.depth - 1) * (
                        '*** ' if obj == self.instance else '--- '),
                    obj,
                ),
            ) for obj in self.fields['of'].queryset
        ]

    def clean(self):
        data = super(MoveForm, self).clean()
        if not data.get('move_to'):
            return data

        if data.get('of') and data.get('of') == self.instance:
            raise forms.ValidationError({
                'of': _('Cannot move node to a position relative to itself.'),
            })

        if not data.get('of'):
            self.instance.parent = None
        elif data['move_to'] in ('left', 'right'):
            self.instance.parent = data.get('of').parent
        else:
            self.instance.parent = data.get('of')

        self.instance.full_clean()

        return data

    def save(self):
        siblings = list(self.model.objects.filter(
            parent=self.instance.parent,
        ).exclude(
            pk=self.instance.pk,
        ))
        of = self.cleaned_data['of']
        move_to = self.cleaned_data['move_to']

        if move_to == 'first' or (not of and move_to == 'left'):
            siblings.insert(0, self.instance)
        elif move_to == 'last' or (not of and move_to == 'right'):
            siblings.append(self.instance)
        elif move_to == 'left':
            siblings.insert(siblings.index(of), self.instance)
        elif move_to == 'right':
            siblings.insert(siblings.index(of) + 1, self.instance)

        for index, instance in enumerate(siblings):
            if instance == self.instance:
                instance.position = (index + 1) * 10
                instance.save()
            else:
                self.model.objects.filter(pk=instance.pk).update(
                    position=(index + 1) * 10,
                )
