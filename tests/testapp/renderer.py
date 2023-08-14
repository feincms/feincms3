from feincms3.plugins import external, html, richtext
from feincms3.regions import Regions
from feincms3.renderer import TemplatePluginRenderer
from testapp.models import HTML, External, Image, RichText, Snippet


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(RichText, richtext.render_richtext)
renderer.register_template_renderer(Image, "renderer/image.html")
Snippet.register_with(renderer)
renderer.register_string_renderer(External, external.render_external)
renderer.register_string_renderer(HTML, html.render_html)


def page_context(request, *, page):
    return {
        "page": page,
        "page_regions": Regions.from_item(
            item=page,
            renderer=renderer,
            inherit_from=page.ancestors().reverse(),
        ),
    }
