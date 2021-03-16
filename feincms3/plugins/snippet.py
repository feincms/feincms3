"""
Plugin for including template snippets through the CMS
"""

from collections import defaultdict

from content_editor.admin import ContentEditorInline
from django.db import models
from django.db.models import signals
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


__all__ = ("Snippet", "SnippetInline", "render_snippet")


def render_snippet(plugin, **kwargs):
    """
    Renders the selected template using ``render_to_string``
    """
    return render_to_string(plugin.template_name, {"plugin": plugin})


class Snippet(models.Model):
    """
    Template snippet plugin
    """

    template_name = models.CharField(
        _("template"),
        max_length=200,
        choices=(("", ""),),  # Non-empty choices for get_*_display
    )

    class Meta:
        abstract = True
        verbose_name = _("predefined snippet")
        verbose_name_plural = _("predefined snippets")

    def __str__(self):
        return "{}".format(self.get_template_name_display())

    @staticmethod
    def fill_template_name_choices(sender, **kwargs):
        """
        Fills in the choices for ``template_name`` from the ``TEMPLATES`` class
        variable. This method is a receiver of Django's ``class_prepared``
        signal.
        """
        if issubclass(sender, Snippet) and not sender._meta.abstract:
            sender._meta.get_field("template_name").choices = [
                choice[:2] for choice in sender.TEMPLATES
            ]

    @classmethod
    def register_with(cls, renderer):
        """
        This helper registers the snippet plugin with a
        ``TemplatePluginRenderer`` while adding support for template-specific
        context functions. The templates specified using the ``TEMPLATES``
        class variable may contain a callable which receives the plugin
        instance and the template context and returns a context dictionary.
        """
        from feincms3.renderer import default_context

        context_fns = defaultdict(
            lambda: default_context,
            [(row[0], row[2]) for row in cls.TEMPLATES if len(row) > 2],
        )

        renderer.register_template_renderer(
            cls,
            lambda plugin: plugin.template_name,
            lambda plugin, context: context_fns[plugin.template_name](plugin, context),
        )


signals.class_prepared.connect(Snippet.fill_template_name_choices)


class SnippetInline(ContentEditorInline):
    """
    Snippet inline does nothing special, it simply exists for consistency
    with the other feincms3 plugins
    """

    pass
