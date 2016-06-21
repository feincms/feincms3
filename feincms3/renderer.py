from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from django.db.models import Model
from django.utils.html import conditional_escape, mark_safe


class PluginRenderer(object):
    def __init__(self):
        self._renderers = OrderedDict(((
            Model,
            lambda plugin: mark_safe('<!-- %s: %s -->' % (
                plugin._meta.label,
                plugin,
            )),
        ),))

    def register(self, plugin, renderer):
        self._renderers[plugin] = renderer

    def render(self, contents):
        return mark_safe(''.join(
            conditional_escape(self.render_content(c)) for c in contents
        ))

    def render_content(self, content):
        if content.__class__ not in self._renderers:
            for plugin, renderer in reversed(  # pragma: no branch
                    list(self._renderers.items())):
                if isinstance(content, plugin):
                    self.register(content.__class__, renderer)
                    break
        return self._renderers[content.__class__](content)
