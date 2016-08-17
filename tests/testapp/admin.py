from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditor

from mptt.admin import DraggableMPTTAdmin

from feincms3 import plugins

from . import models


@admin.register(models.Page)
class PageAdmin(DraggableMPTTAdmin, ContentEditor):
    list_display = [
        'tree_actions', 'indented_title',
        'is_active', 'menu',
        'language_code',
        'template_key',
        'application',
    ]
    list_filter = ['is_active', 'menu']
    list_editable = ['is_active']
    list_display_links = ['indented_title']
    prepopulated_fields = {
        'slug': ('title',),
    }
    radio_fields = {
        'menu': admin.HORIZONTAL,
        'language_code': admin.HORIZONTAL,
        'template_key': admin.HORIZONTAL,
        'application': admin.HORIZONTAL,
    }
    raw_id_fields = ['parent']

    mptt_level_indent = 30

    fieldsets = [
        (None, {
            'fields': (
                'is_active',
                'title',
                'parent',
            )
        }),
        (capfirst(_('path')), {
            'fields': (
                'slug',
                'static_path',
                'path',
            ),
            'classes': ('tabbed',),
        }),
        (capfirst(_('settings')), {
            'fields': (
                'menu',
                'language_code',
                'template_key',
                'application',
            ),
            'classes': ('tabbed',),
        }),
    ]

    inlines = [
        plugins.RichTextInline.create(model=models.RichText),
        plugins.ImageInline.create(model=models.Image),
        plugins.SnippetInline.create(model=models.Snippet),
        plugins.ExternalInline.create(model=models.External),
    ]

    class Media:
        css = {'all': (
            'https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css',  # noqa
        )}
        js = (
            'app/plugin_buttons.js',
        )
