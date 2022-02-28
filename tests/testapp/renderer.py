from feincms3.plugins import external, html, richtext
from feincms3.renderer import TemplatePluginRenderer

from .models import HTML, External, Image, RichText, Snippet


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(RichText, richtext.render_richtext)
renderer.register_template_renderer(Image, "renderer/image.html")
Snippet.register_with(renderer)
renderer.register_string_renderer(External, external.render_external)
renderer.register_string_renderer(HTML, html.render_html)
