Rendering
=========

The default behavior of feincms3's renderer is to concatenate the
rendered result of individual plugins into one long HTML string.

That may not always be what you want. This guide also describes a few
alternative methods of rendering plugins that may or may not be useful.


Rendering plugins
~~~~~~~~~~~~~~~~~

The :class:`feincms3.renderer.RegionRenderer` offers two
fundamental ways of rendering content, string renderers and template
renderers. The former simply return a string, the latter work similar to
``{% include %}``.


String renderers
----------------

You may register a rendering function which returns a HTML string:

.. code-block:: python

    from django.utils.html import mark_safe
    from app.pages.models import RichText

    renderer = RegionRenderer()
    renderer.register(
        RichText,
        lambda plugin, context: mark_safe(plugin.text)
    )

Template renderers
------------------

Or you may choose to render plugins using a template:

.. code-block:: python

    from feincms3.renderer import template_renderer

    renderer.register(
        Image,
        template_renderer("plugins/image.html"),
    )

The configured template receives the plugin instance as ``"plugin"``.

If you need more flexibility you may define your own plugin renderer:

.. code-block:: python

    from feincms3.renderer import render_in_context

    def external_using_template(plugin, context):
        if "youtube" in plugin.url:
            template_name = "plugin/youtube.html"
        elif "vimeo" in plugin.url
            template_name = "plugin/vimeo.html"
        else:
            template_name = "plugin/external.html"
        return render_in_context(context, template_name, {"plugin": plugin})

    renderer.register(
        External,
        external_using_template,
    )

.. note::

   You could also render the plugin using ``render_to_string`` but
   ``render_in_context`` has the advantage that it makes the surrounding
   context (using all context processors etc.) available, at least when using
   the ``{% render_region %}`` template tag.

Often, having the surrounding template context and the plugin instance
available inside the template is enough. However, you might want to
provide additional context variables. This can be achieved by specifying
the ``context`` function. The function receives the plugin instance and
the surrounding template context:

.. code-block:: python

    from feincms3.renderer import template_renderer

    def plugin_context(plugin, context):
        return {
            "plugin": plugin,  # Recommended, but not required.
            "additional": ....
        }

    renderer.register(
        Plugin,
        template_renderer("plugin/plugin.html", plugin_context),
    )


Rendering individual plugins
----------------------------

Rendering individual plugin instances is possible using the
``render_plugin`` method. Except if you're using a
non-standard ``RegionRenderer`` class used to encapsulate the fetching of
plugins and rendering of regions you won't have to know about this
method, but see below under :ref:`grouping-plugins-into-subregions`.


Regions instances
-----------------

Because fetching plugins may be expensive (at least one database query
per plugin type) it makes sense to avoid fetching plugins if there is a
valid cached version. The :class:`feincms3.regions.RegionRenderer` which
handles the specifics of rendering plugins belonging to specific regions
has a method, ``RegionRenderer.regions_from_item``, which automatically creates
a lazily evaluated :class:`content_editor.contents.Contents` instance.

By inspecting the plugins registered with the renderer the regions
instance automatically knows which plugins to load. It also supports
inherited regions introduced in the :ref:`more-regions` section
of the :ref:`templates-and-regions` guide.

The object returned by ``regions_from_item`` (and ``regions_from_contents``)
has one method which we'll concern ourselves with right now,
``.render(region)``. This method is used to render one single region. When
passing a ``timeout`` argument to the ``RegionRenderer.regions_from_item``
factory method all return values of ``.render(region)`` are automatically
cached.


Rendering regions in the template
---------------------------------

To render regions in the template, the template first requires the
``regions`` instance:

.. code-block:: python

    from .renderer import renderer

    def page_detail(request, path=None):
        page = ...
        ...
        return render(
            request,
            ...,
            {
                "page": page,
                "regions": renderer.regions_from_item(page, timeout=60),
            },
        )

In the template you can now use the template tag:

.. code-block:: html

    {% load feincms3 %}

    {% render_region regions "main" %}

Using the template tag is advantageous because it automatically provides
the surrounding template context to individual plugins' templates,
meaning that they could for example access the ``request`` instance if
e.g. an API key would be different for different URLs.

.. note::
   Caching either works for all regions  or for none at all.


.. _grouping-plugins-into-subregions:

Grouping plugins into subregions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Regions`` class supports rendering subregions differently. Plugins
may be grouped automatically by their type or by some attribute they
share.

Let's make an example. Assume that we want to group adjacent teaser
elements. We have several teaser plugins but they all share the same
``subregion`` attribute value:

.. code-block:: python

    class ArticleTeaser(PagePlugin):
        article = models.ForeignKey(...)

    class ProjectTeaser(PagePlugin):
        project = models.ForeignKey(...)

Next, we have to define a regions class which knows how to handle those
teasers. The name of the handler has to match the subregion attribute
exactly:

.. code-block:: python

    from feincms3.renderer import RegionRenderer

    class SmartRegionRenderer(RegionRenderer):
        def handle_teasers(self, plugins, context):
            # Start the teasers element:
            yield '<div class="teasers">'
            for plugin in self.takewhile(plugins, subregion="teasers"):
                # items is a deque, render the leftmost item:
                yield self.render_plugin(plugin, context)
            yield "</div>"

    renderer = SmartRegionRenderer()
    renderer.register(ArticleTeaser, ..., subregion="teasers")
    renderer.register(ProjectTeaser, ..., subregion="teasers")


Grouping plugins into containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The previous example added an ``<div class="teasers">...</div>`` wrapper
element to a group of teasers. However, sometimes you want to allow some
plugins to escape the containing element. In this case it may be useful
to override the default subregions handler instead:

.. code-block:: python

    from django.utils.html import mark_safe

    from feincms3.renderer import RegionRenderer

    class FullWidthPlugin(PagePlugin):
        pass

    class ContainerAwareRegionRenderer(RegionRenderer):
        def handle_default(self, plugins, context):
            yield '<div class="container">'
            for plugin self.takewhile(plugins, subregion="default"):
                yield self.render_plugin(plugin, context)
            yield "</div>"

        def handle_fullwidth(self, plugins, context):
            for plugin self.takewhile(plugins, subregion="fullwidth"):
                yield self.render_plugin(plugins.popleft(), context)

    # Instantiate renderer and register plugins
    renderer = ContainerAwareRegionRenderer()
    renderer.register(FullWidthPlugin, ..., subregion="fullwidth")

    # Use our new regions class, not the default
    regions = renderer.regions_from_item(page)


Generating JSON
~~~~~~~~~~~~~~~

A different real-world example is generating JSON instead of HTML. This
is possible with a custom ``Regions`` class too:

.. code-block:: python

    from feincms3.regions import RegionRenderer

    class JSONRegionRenderer(RegionRenderer):
        def render_region(self, *, region, contents, context):
            return [
                dict(
                    self.render_plugin(plugin, context),
                    type=plugin.__class__.__name__,
                )
                for plugin in contents[region.key]
            ]

            # Alternatively (In this case the ``type`` key above would have to be
            # provided by the renderers themselves):
            # return list(self.generate(self.contents[region], context))

    def page_content(request, pk):
        page = get_object_or_404(Page, pk=pk)

        renderer = JSONRegionRenderer()
        renderer.register(
            RichText,
            lambda plugin, context: {"text": plugin.text},
        )
        renderer.register(
            Image,
            lambda plugin, context: {"image": request.build_absolute_uri(plugin.image.url)},
        )

        regions = renderer.regions_from_item(page, timeout=60)

        return JsonResponse({
            "title": page.title,
            "content": regions.render("main", None),
        })

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
