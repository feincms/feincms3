Rendering
=========

The default behavior of feincms3's renderer is to concatenate the
rendered result of individual plugins into one long HTML string.

That may not always be what you want. This guide also describes a few
alternative methods of rendering plugins that may or may not be useful.


Rendering plugins
~~~~~~~~~~~~~~~~~

The :class:`feincms3.renderer.TemplatePluginRenderer`` offers two
fundamental ways of rendering content.

String renderers
----------------

You may register a rendering function which returns a HTML string:

.. code-block:: python

    from django.utils.html import mark_safe
    from app.pages.models import RichText

    renderer = TemplatePluginRenderer()
    renderer.register_string_renderer(
        RichText,
        lambda plugin: mark_safe(plugin.text)
    )

Template renderers
------------------

Or you may choose to render plugins using a template:

.. code-block:: python

    renderer.register_template_renderer(
        Image,
        "plugins/image.html",
    )

The configured template receives the plugin instance as ``"plugin"``
(fittingly).

If you need more flexibility, also accepts a callable as
``template_name``:

.. code-block:: python

    def external_template_name(plugin):
        if "youtube" in plugin.url:
            return "plugin/youtube.html"
        elif "vimeo" in plugin.url
            return "plugin/vimeo.html"
        return "plugin/external.html"

    renderer.register_template_renderer(
        External,
        external_template_name
    )

The third argument, ``context`` may be used to provide a different
context for plugins. If ``context`` is a callable it receives the plugin
instance and, if provided to the renderer itself, the rendering context
of the outer template.


Rendering individual plugins
----------------------------

Rendering individual plugin instances is possible using the
``render_plugin_in_context`` method. Except if you're overriding the
``Regions`` instance used to encapsulate the fetching of plugins and
rendering of regions you won't have to know about this method, but see
below under :ref:`rendering-plugins-differently`.


Regions instances
-----------------

Because fetching plugins may be expensive (at least one database query
per plugin type) it makes sense to avoid fetching plugins if they are
not required. The ``TemplatePluginRenderer.regions(item)`` method returns a
:class:`feincms3.renderer.Regions` instance containing a lazily
evaluated :class:`content_editor.contents.Contents` instance with all
plugins of the item and optionally also of related items when using the
``inherit_from`` argument introduced in the :ref:`more-regions` section
of the :ref:`templates-and-regions` guide.

.. note::
   The regions of this ``Regions`` class have a different meaning than
   the ``Region`` class used to define regions for the content editor.

   The former encapsulates plugin instances and their fetching and
   rendering (per region of course), the latter describes the region
   itself.

The Regions instance mainly has one interesting method,
``Regions.render(region)``, used to render one single region. The
default implementation is wrapped by
:func:`~feincms3.renderer.cached_render`, which means that when passing
a ``timeout`` argument you'll get the benefits of caching for free.


Rendering regions in the template
---------------------------------

To render regions in the template, the template first requires the
``regions`` instance:

.. code-block:: python

    def page_detail(request, path=None):
        page = ...
        ...
        return render(request, ..., {
            "page": page,
            "regions": renderer.regions(page),
        })

In the template you can now use the template tag:

.. code-block:: html

    {% load feincms3_renderer %}

    {% render_region regions "main" %}

    {# Or better yet: #}

    {% render_region regions "main" timeout=30 %}

Using the template tag is advantageous because it automatically provides
the surrounding template context to individual plugins' templates,
meaning that they could for example access the ``request`` instance if
e.g. an API key would be different for different URLs.

.. note::
   Caching either works for all regions in a ``Regions`` instance or for
   none at all. Either use ``timeout`` everywhere, or nowhere -- except
   if the rendering itself would be expensive, and not the database
   roundtrips.


.. _rendering-plugins-differently:

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

.. note::
   The :mod:`incubator <feincms3.incubator>` offers an experimental but
   more flexible and powerful system for rendering sections differently.


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

In this particular example ``register_string_renderer`` is a bit of a
misnomer. For string renderers, ``renderer.render_plugin_in_context``
returns the return value of the individual renderer as-is.

.. note::
   A different method would have been to use lower-level methods from
   django-content-editor. A short example follows, however there's more
   left to do to reach the state of the example above such as caching:

   .. code-block:: python

       from content_editor.contents import contents_for_items

       renderers = {
           RichText: lambda plugin: {
               "text": plugin.text
           },
           Image: lambda plugin: {
               "image": request.build_absolute_uri(plugin.image.url)
           },
       }
       contents = contents_for_item(page, [RichText, Image])
       data = [
           dict(
               renderers[plugin.__class__](plugin),
               type=plugin.__class__.__name__
           )
           for plugin in contents.main
       ]
       # etc...
