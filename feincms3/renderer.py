"""
The region renderer lives in ``content_editor.renderer`` since
django-content-editor 10.0. This module re-exports it and adds deprecated
compatibility APIs and the closer-based section rendering.
"""

import warnings

from content_editor import renderer as _content_editor_renderer
from content_editor.renderer import (
    PluginNotRegisteredError,
    default_context,
    render_in_context,
    template_renderer,
)


__all__ = (
    "PluginNotRegisteredError",
    "RegionRenderer",
    "TemplatePluginRenderer",
    "default_context",
    "render_in_context",
    "template_renderer",
)


# Backwards compatibility
PluginNotRegistered = PluginNotRegisteredError

_CLOSE_SECTION = "_close_section"


class RegionRenderer(_content_editor_renderer.RegionRenderer):
    """
    :class:`content_editor.renderer.RegionRenderer` with deprecated
    compatibility APIs and the deprecated closer-based section rendering.
    """

    @property
    def handlers(self):
        warnings.warn(
            "The handlers aren't really supposed to be public. Access _handlers if you know what you're doing or propose a better API instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._handlers

    # Closer-based sections support (deprecated, use containers instead)

    def render_section_plugins(self, section, plugins, context):
        """
        Render the plugins of a closer-based section until the next section
        closing plugin or the end of the region.

        Deprecated: closer-based sections are replaced by containers, see the
        django-content-editor documentation. Data is migrated using
        ``content_editor.migrations_utils.compute_depths``.
        """
        warnings.warn(
            "Closer-based sections are deprecated. Set `container = True` on"
            " the models of plugins opening sections and use"
            " content_editor.migrations_utils.compute_depths to migrate the data.",
            DeprecationWarning,
            stacklevel=2,
        )
        out = []
        while plugins:
            subregion = self.subregion(plugins[0])
            if subregion is _CLOSE_SECTION:
                plugins.popleft()
                break
            elif subregion is not None:
                out.extend(self._handlers[subregion](plugins, context))
            else:
                out.append(self.render_plugin(plugins.popleft(), context))
        return out

    def register_section_close(self, plugin, renderer="", **kwargs):
        """
        Register a plugin closing closer-based sections. Deprecated, see
        :meth:`render_section_plugins`.
        """
        warnings.warn(
            "Closer-based sections are deprecated. Set `container = True` on"
            " the models of plugins opening sections and use"
            " content_editor.migrations_utils.compute_depths to migrate the data.",
            DeprecationWarning,
            stacklevel=2,
        )
        kwargs["subregion"] = _CLOSE_SECTION
        self.register(plugin, renderer, **kwargs)

    def handle__close_section(self, plugins, context):
        plugins.popleft()
        yield from ()

    # TemplatePluginRenderer compatibility

    def register_string_renderer(self, plugin, renderer):
        """Backwards compatibility for ``TemplatePluginRenderer``. It is
        deprecated, don't use in new code."""
        warnings.warn(
            "register_string_renderer is deprecated. Use register instead."
            " (Hint: register_string_renderer(plugin, renderer) can be replaced by"
            " register(plugin, renderer) most of the time. The renderer has to be"
            " changed to accept an additional `context` argument.)",
            DeprecationWarning,
            stacklevel=2,
        )
        if callable(renderer):
            self.register(plugin, lambda plugin, context: renderer(plugin))
        else:
            self.register(plugin, renderer)

    def register_template_renderer(
        self, plugin, template_name, context=default_context
    ):
        """Backwards compatibility for ``TemplatePluginRenderer``. It is
        deprecated, don't use in new code."""
        warnings.warn(
            "register_template_renderer is deprecated. Use register instead."
            " (Hint: register_template_renderer(plugin, template_name, local_context)"
            " can be replaced by register(plugin, template_renderer(template_name, local_context))"
            " most of the time.)",
            DeprecationWarning,
            stacklevel=2,
        )
        self.register(plugin, _compat_template_renderer(template_name, context))

    def render_plugin_in_context(self, plugin, context=None):
        """Backwards compatibility for ``TemplatePluginRenderer``. It is
        deprecated, don't use in new code."""
        warnings.warn(
            "render_plugin_in_context is deprecated. Use render_plugin instead."
            " (Hint: render_plugin works exactly the same except that the `context` argument"
            " is required.)",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.render_plugin(plugin, context)


def _compat_template_renderer(_tpl, _ctx=default_context, /):
    """Compatibility implementation which accepts an optionally callable
    template and an optionally callable context function."""

    def renderer(plugin, context):
        template_name = _tpl(plugin) if callable(_tpl) else _tpl
        local_context = _ctx(plugin, context) if callable(_ctx) else _ctx
        return render_in_context(context, template_name, local_context)

    return renderer


class TemplatePluginRenderer(RegionRenderer):
    """
    TemplatePluginRenderer is a deprecated alias for
    :class:`~feincms3.renderer.RegionRenderer`.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "TemplatePluginRenderer is a deprecated alias for the new RegionRenderer."
            " (Hint: An incremental upgrade is supported. You can start by"
            " replacing TemplatePluginRenderer with RegionRenderer.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
