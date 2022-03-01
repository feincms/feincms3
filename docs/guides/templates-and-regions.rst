.. _templates-and-regions:

Templates and regions
=====================

The build-your-CMS guide only used one region and one template. However,
this isn't sufficient for many sites. Some sites have a moodboard region
and maybe a sidebar region; some sites at least have a different layout
on the home page and so on.


.. _more-regions:

More regions
~~~~~~~~~~~~

django-content-editor requires a ``regions`` attribute or property on
the model containing a list of ``Region`` instances.  The
:ref:`build-your-cms` guide presented a page model with only a single
region, ``"main"``. It is of course possible to specify more regions:

.. code-block:: python

    class Page(AbstractPage):
        regions = [
            Region(key="main", title=_("Main")),
            Region(key="sidebar", title=_("Sidebar"), inherited=True),
        ]

Regions may also be marked as ``inherited``. This means that pages
deeper down in the tree may inherit content from some other page
(normally the page's ancestors) in case the page region itself does not
define any content.

The ``page_detail`` view presented in the guide also works with more
than one region. However, for region inheritance to work you have to
provide the pages whose content should be inherited yourself. There
isn't much to do though, just add the ``inherit_from`` keyword argument:

.. code-block:: python

    def page_detail(request, path=None):
        page = ...
        return render(
            request,
            "pages/standard.html",
            {
                "page": page,
                "regions": renderer.regions_from_item(
                    page,
                    inherit_from=page.ancestors().reverse(),
                ),
            },
        )

``page.ancestors().reverse()`` returns ancestors ordered from the page's
parent to the root of the tree. We want pages to inherit content from
their closest possible ancestors.


Making templates selectable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

As written in the introduction above, sometimes a single template or
layout isn't enough. Enter the :class:`~feincms3.mixins.TemplateMixin`:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from content_editor.models import Region
    from feincms3.applications import PageTypeMixin, TemplateType
    from feincms3.pages import AbstractPage

    class Page(AbstractPage, PageTypeMixin):
        TYPES = [
            TemplateType(
                key="standard",
                title=_("standard"),
                template_name="pages/standard.html",
                regions=(
                    Region(key="main", title=_("Main")),
                ),
            ),
            TemplateType(
                key="with-sidebar",
                title=_("with sidebar"),
                template_name="pages/with-sidebar.html",
                regions=[
                    Region(key="main", title=_("Main")),
                    Region(key="sidebar", title=_("Sidebar"), inherited=True),
                ],
            ),
        ]

The ``regions`` attribute is provided by the ``PageTypeMixin`` and must be
removed from the ``Page`` definition. Additionally, the ``TemplateMixin``
provides a ``type`` property returning the currently selected page type.
Instead of hard-coding the template we should now change the ``page_detail``
view to render the selected template, ``page.type.template_name``:

.. code-block:: python

    def page_detail(request, path=None):
        page = ...
        return render(
            request,
            page.type.template_name,
            {
                "page": page,
                "regions": renderer.regions_from_item(
                    page,
                    inherit_from=page.ancestors().reverse(),
                ),
            },
        )
