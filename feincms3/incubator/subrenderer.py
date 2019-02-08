"""
Subrenderers
~~~~~~~~~~~~

Subrenderers allow rendering sections inside regions using different renderers.
The same plugin may be rendered differently in different contexts. Sometimes
just differentiating on the plugin itself or inserting additional elements as
described in :ref:`rendering-plugins-differently` is sufficient, but you might
want to try a more powerful tool.

Let's make an example. Assume that we want to show a list of boxes, where a box
might either be a teaser for a different page in the CMS or it might lead
directly to a file download. Files can be integrated everywhere on the site,
but they are generally rendered in a less obtrusive way, except inside our
boxes list.

Defining a subrenderer
----------------------

A boxes renderer definition and instantiation follows:

.. code-block:: python

    from . import models
    from feincms3.incubator import subrenderer
    from feincms3.renderer import TemplatePluginRenderer

    class BoxRenderer(subrenderer.Subrenderer):
        # .enter() and .exit() are not required, but are very useful to add
        # wrapping elements to sections rendered by the subrenderer
        def enter(self, **kwargs):
            yield '<div class="boxes">'

        def exit(self, **kwargs):
            yield "</div>"

    box_renderer = BoxRenderer()
    box_renderer.register_template_renderer(
        models.PageTeaser,
        "boxes/page-teaser.html",
    )
    box_renderer.register_template_renderer(
        models.File,
        "boxes/file.html",
    )

Making the subrenderer known to the main renderer
-------------------------------------------------

Next, we need a ``Regions`` class instantiated by the main renderer, but which
also knows about subrenderers:

.. code-block:: python

    class Regions(subrenderer.SubrendererRegions):
        subrenderers = {"boxes": box_renderer}  # The exact key is important!

    renderer = TemplatePluginRenderer(regions_class=Regions)

The plugins have to be registered with the main renderer even if the main
renderer does not render some plugins -- the renderer provides the list of
plugins to be loaded from the database:

.. code-block:: python

    # When rendered by the main renderer page teasers do not produce any output
    renderer.register_string_renderer(
        models.PageTeaser,
        "",
    )
    renderer.register_template_renderer(
        models.File,
        "plugins/file.html",  # Different template than above!
    )

Entering the subrenderer
------------------------

During rendering a subrenderer is activated when the ``SubrendererRegions``
encounters a plugin with a ``"subrenderer"`` attribute. In our case, two
attribute values are allowed:

1. ``"boxes"``: Activates the ``box_renderer`` for the current plugin.
2. A falsy value for exiting the subrenderer again.

Probably the best way to achieve 1. in our example would be to add the
attribute to the page teaser in the class definition:

.. code-block:: python

    # ...
    class PageTeaser(PagePlugin):
        subrenderer = "boxes"

        # ...

Of course making the "subrenderer" attribute a model field or a property would
work too.

Exiting the subrenderer
-----------------------

The subrenderer is deactivated if any of the following conditions occurs:

- ``SubrendererRegions`` encounters a plugin with a ``"subrenderer"`` attribute
  which does not correspond to the current subrenderer.
- The current subrenderer does not accept a plugin. By default this happens
  when the plugin has not been registered with the subrenderer.
- Rendering finishes (no more contents).

Code documentation
------------------

"""

import warnings

from django.utils.html import mark_safe

from feincms3.renderer import Regions, TemplatePluginRenderer, cached_render


__all__ = ("Subrenderer", "SubrendererRegions")


warnings.warn(
    "The subrenderer module will be removed. Please start using"
    " the subregions feature of feincms3.regions.Regions instead.",
    DeprecationWarning,
    stacklevel=2,
)


class Subrenderer(TemplatePluginRenderer):
    """
    ``TemplatePluginRenderer`` subclass with hooks for adding wrapping elements
    and for rejecting plugin types
    """

    def accepts(self, plugin, context=None):
        """
        Returns ``True`` if plugin is of a handleable type

        Returning ``False`` exits the subrenderer.
        """
        return plugin.__class__ in self._renderers

    def enter(self, **kwargs):
        """
        Hook for opening a wrapping element
        """
        yield ""  # pragma: no cover

    def exit(self, **kwargs):
        """
        Hook for closing a wrapping element
        """
        yield ""  # pragma: no cover

    def reenter(self, **kwargs):
        """
        If a plugin has a ``subrenderer`` attribute corresponding to the
        current subrenderer the subrenderer does not change by design. However,
        under some circumstances it may be useful to exit the subrenderer and
        enter it again right away. This is made possible by this hook. Most
        implementations will probably simply ``yield from self.exit(**kwargs)``
        and ``yield from self.enter(**kwargs)``.
        """
        yield ""


class SubrendererRegions(Regions):
    """
    ``Regions`` subclass containing the logic enter and exit subrenderers
    depending on plugins
    """

    #: Map of subrenderer keys to subrenderer instances
    subrenderers = {}
    #: Holds current subrenderer or ``None`` if using main renderer at the
    #: moment
    current = None

    def activate(self, subrenderer, **kwargs):
        """
        Sets the passed subrenderer instance as current subrenderer, or exits
        a subrenderer if passed ``None``.

        Handles eventually required subrenderer enter and exit hooks calls.
        """
        if self.current:
            yield from self.current.exit(**kwargs)
        self.current = subrenderer
        if self.current:
            yield from self.current.enter(**kwargs)

    @cached_render
    def render(self, region, context=None):
        def _generator():
            for plugin in self._contents[region]:
                if hasattr(plugin, "subrenderer"):
                    new = (
                        self.subrenderers[plugin.subrenderer]
                        if plugin.subrenderer
                        else None
                    )
                    if new != self.current:  # Move to different subrenderer?
                        yield from self.activate(
                            new, plugin=plugin, context=context, region=region
                        )
                    elif self.current:  # Re-enter
                        yield from self.current.reenter(
                            plugin=plugin, context=context, region=region
                        )

                if self.current:
                    if self.current.accepts(plugin, context):
                        yield self.current.render_plugin_in_context(plugin, context)
                        continue  # Subrenderer success! Process next plugin.
                    else:
                        yield from self.activate(None, context=context, region=region)

                # No current subrenderer. Use main renderer.
                yield self._renderer.render_plugin_in_context(plugin, context)

            yield from self.activate(None, context=context, region=region)

        return mark_safe("".join(_generator()))
