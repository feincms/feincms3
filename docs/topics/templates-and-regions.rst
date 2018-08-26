Templates and regions
=====================

The build-your-CMS guide only used one region and one template. However,
this isn't sufficient for many sites. Many sites have a moodboard region
and maybe a sidebar region; many sites at least have a different layout
on the home page and so on.


Making templates selectable
~~~~~~~~~~~~~~~~~~~~~~~~~~~


Inherited regions
~~~~~~~~~~~~~~~~~

``renderer.regions(page, inherit_from=page.ancestors().reverse())``
