Customizing rendering
=====================

The default behavior of feincms3's renderer is to concatenate the
rendered result of individual plugins into one long HTML string.

That may not always be what you want. This guide describes a few
alternative methods of rendering plugins that may or may not be useful.


Rendering some plugins differently
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose you're building a site where some plugins should go over the
full width of the browser window, but most plugins are constrained
inside a container. One way to solve this problem would be to make each
plugin open and close its own container. That may work well. A different
possibility would be to make the renderer smarter. Let's build a custom
``Regions`` subclass which knows how to make some plugins escape the
container:

.. code-block:: python

    from django.utils.html import mark_safe

    from feincms3 import renderer


    class ContainerAwareRegions(renderer.Regions):
        def is_full_width(self, plugin):
            # Add your own logic here, e.g.:
            return getattr(plugin, "is_full_width", False)

        # @cached_render is not strictly necessary, but you might want
        # to use the ``timeout`` argument to ``render_region``...
        @renderer.cached_render
        def render(self, region, context=None):
            html = []
            outside = True

            for plugin in self._contents[region]:
                output = self._renderer.render_plugin_in_context(plugin, context)
                if self.is_full_width(plugin) and not outside:
                    html.extend([
                        "</div>",  # Close the surrounding container
                        output,
                    ])
                    outside = True
                elif not self.is_full_width(plugin) and outside:
                    html.extend([
                        '<div class="container">',  # Open a new container
                        output,
                    ])
                    outside = False
                else:
                    html.append(output)

            if not outside:
                # If still inside, close the container again.
                html.append("</div>")

            return mark_safe("".join(html))

    # When instantiating the TemplatePluginRenderer, use:
    renderer = TemplatePluginRenderer(regions_class=ContainerAwareRegions)


Generating JSON
~~~~~~~~~~~~~~~

A different real-world example is generating JSON instead of HTML. This
is possible with a custom ``Regions`` class too:

.. code-block:: python

    from feincms3 import renderer

    class JSONRegions(Regions):
        @renderer.cached_render
        def render(self, region):  # No context in this example -- possible as well
            return [
                dict(
                    self._renderer.render_plugin_in_context(plugin),
                    type=plugin.__class__.__name__,
                )
                for plugin in self._contents[region]
            ]

    def page_content(request, pk):
        page = get_object_or_404(Page, pk=pk)

        renderer = TemplatePluginRenderer(regions=JSONRegions)
        renderer.register_string_renderer(
            RichText,
            lambda plugin: {"text": plugin.text},
        )
        renderer.register_string_renderer(
            Image,
            lambda plugin: {"image": request.build_absolute_uri(plugin.image.url)},
        )

        return JsonResponse({
            "title": page.title,
            "content": regions.render("content", timeout=60),
        })


Outlook
~~~~~~~

Of course this was just a short demonstration of the possibilities. It
would also be possible to insert e.g. a ``RenderingCommandPlugin`` which
has no output of its own but only changes state in the renderer, or use
a finite state machine for rendering. (I'd love to hear examples of
things you did using this facility!)
