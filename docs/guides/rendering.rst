Rendering
=========

The default behavior of feincms3's renderer is to concatenate the
rendered result of individual plugins into one long HTML string.

That may not always be what you want. This guide also describes a few
alternative methods of rendering plugins that may or may not be useful.


Rendering plugins
~~~~~~~~~~~~~~~~~

The :class:`feincms3.renderer.TemplatePluginRenderer` offers two
fundamental ways of rendering content, string renderers and template
renderers. The former simply return a string, the latter work similar to
``{% include %}``.


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

The configured template receives the plugin instance as ``"plugin"``.

If you need more flexibility you may also pass a callable instead of a
template path as ``template_name``. The callable receives the plugin
instance as its only argument:

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

Often, having the surrounding template context and the plugin instance
available inside the template is enough. However, you might want to
provide additional context variables. This can be achieved by specifying
the ``context`` function. The function receives the plugin instance and
the surrounding template context:

.. code-block:: python

    def plugin_context(plugin, context):
        return {
            "plugin": plugin,  # Recommended, but not required.
            "additional": ....
        }

    renderer.register_template_renderer(
        Plugin,
        "plugin/plugin.html",
        plugin_context,
    )


Rendering individual plugins
----------------------------

Rendering individual plugin instances is possible using the
``render_plugin_in_context`` method. Except if you're using a
non-standard ``Regions`` class used to encapsulate the fetching of
plugins and rendering of regions you won't have to know about this
method, but see below under :ref:`grouping-plugins-into-subregions`.


Regions instances
-----------------

Because fetching plugins may be expensive (at least one database query
per plugin type) it makes sense to avoid fetching plugins if there is a
valid cached version. The :class:`feincms3.regions.Regions` which
handles the specifics of rendering plugins belonging to specific regions
has a factory method, ``Regions.from_item``, which automatically creates
a lazily evaluated :class:`content_editor.contents.Contents` instance.

By inspecting the plugins registered with the renderer the regions
instance automatically knows which plugins to load. It also supports
inherited regions introduced in the :ref:`more-regions` section
of the :ref:`templates-and-regions` guide.

.. note::
   The regions of this ``Regions`` class have a different meaning than
   the ``Region`` class used to define regions for the content editor.

   The former encapsulates plugin instances and their fetching and
   rendering (per region of course), the latter describes the region
   itself.

The Regions instance has one method which we'll concern ourselves with
right now, ``Regions.render(region)``. This method is used to render one
single region. When passing a ``timeout`` argument to the
``Regions.from_item`` factory method all return values of
``Regions.render(region)`` are automatically cached.


Rendering regions in the template
---------------------------------

To render regions in the template, the template first requires the
``regions`` instance:

.. code-block:: python

    from feincms3.regions import Regions

    def page_detail(request, path=None):
        page = ...
        ...
        return render(
            request,
            ...,
            {
                "page": page,
                "regions": Regions.from_item(page, renderer, timeout=60),
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
   Caching either works for all regions in a ``Regions`` instance or for
   none at all.


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
        subregion = "teaser"
        article = models.ForeignKey(...)

    class ProjectTeaser(PagePlugin):
        subregion = "teaser"
        project = models.ForeignKey(...)

Next, we have to define a regions class which knows how to handle those
teasers. The name of the handler has to match the subregion attribute
exactly:

.. code-block:: python

    from feincms3.regions import Regions, matches

    class SmartRegions(Regions):
        def handle_teaser(self, items, context):
            # Start the teasers element:
            yield '<div class="teasers">'
            while True:
                # items is a deque, render the leftmost item:
                yield self.renderer.render_plugin_in_context(
                    items.popleft(), context
                )
                if not items:
                    break
                if not matches(items[0], plugins=(ArticleTeaser, ProjectTeaser)):
                    break
            yield "</div>"

Now you'll have to use ``SmartRegions.from_item()`` instead of
``Regions.from_item()``, and that's all there is to it.


Grouping plugins into containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The previous example added an ``<div class="teasers">...</div>`` wrapper
element to a group of teasers. However, sometimes you want to allow some
plugins to escape the containing element. In this case it may be useful
to override the default subregions handler instead:

.. code-block:: python

    from django.utils.html import mark_safe

    from feincms3.regions import Regions, matches

    class FullWidthPlugin(PagePlugin):
        subregion = "fullwidth"

    class ContainerAwareRegions(Regions):
        def handle_default(self, items, context):
            yield '<div class="container">'
            while True:
                yield self.renderer.render_plugin_in_context(
                    items.popleft(), context
                )
                if not items or not matches(items[0], subregions={None, ""}):
                    break
            yield "</div>"

        def handle_fullwidth(self, items, context):
            while True:
                yield self.renderer.render_plugin_in_context(
                    items.popleft(), context
                )
                if not items or not matches(items[0], subregions={"fullwidth"}):
                    break

    # Instantiate renderer and register plugins
    renderer = TemplatePluginRenderer()
    renderer.register_template_renderer(FullWidthPlugin, ...)

    # Use our new regions class, not the default
    regions = ContainerAwareRegions.from_item(page, renderer=renderer)


Generating JSON
~~~~~~~~~~~~~~~

A different real-world example is generating JSON instead of HTML. This
is possible with a custom ``Regions`` class too:

.. code-block:: python

    from feincms3.regions import Regions, cached_render

    class JsonRegions(Regions):
        @cached_render
        def render(self, region, context=None):
            return [
                dict(
                    self.renderer.render_plugin_in_context(plugin),
                    type=plugin.__class__.__name__,
                )
                for plugin in self.contents[region]
            ]

            # Alternatively (In this case the ``type`` key above would have to be
            # provided by the renderers themselves):
            # return list(self.generate(self.contents[region], context))

    def page_content(request, pk):
        page = get_object_or_404(Page, pk=pk)

        renderer = TemplatePluginRenderer()
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
            "content": JsonRegions.from_item(page, renderer=renderer, timeout=60),
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
