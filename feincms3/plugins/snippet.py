from django.db import models
from django.db.models import signals
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditorInline


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
        _("template name"),
        max_length=200,
        choices=(("", ""),),  # Non-empty choices for get_*_display
    )

    class Meta:
        abstract = True
        verbose_name = _("snippet")
        verbose_name_plural = _("snippets")

    def __str__(self):
        return self.get_template_name_display()

    @staticmethod
    def fill_template_name_choices(sender, **kwargs):
        """
        Fills in the choices for ``template_name`` from the ``TEMPLATES`` class
        variable. This method is a receiver of Django's ``class_prepared``
        signal.
        """
        if issubclass(sender, Snippet) and not sender._meta.abstract:
            sender._meta.get_field("template_name").choices = sender.TEMPLATES


signals.class_prepared.connect(Snippet.fill_template_name_choices)


class SnippetInline(ContentEditorInline):
    """
    Snippet inline does nothing special, it simply exists for consistency
    with the other feincms3 plugins
    """

    pass
