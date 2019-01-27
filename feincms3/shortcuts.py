from django.core import paginator
from django.template.response import TemplateResponse


__all__ = ("template_name", "render_list", "render_detail")


def template_name(model, template_name_suffix):
    """
    Given a model and a template name suffix, return the resulting template
    path::

        >>> template_name(Article, '_detail')
        'articles/article_detail.html'
        >>> template_name(User, '_form')
        'auth/user_form.html'
    """

    return "%s/%s%s.html" % (
        model._meta.app_label,
        model._meta.model_name,
        template_name_suffix,
    )


def render_list(
    request, queryset, context=None, *, template_name_suffix="_list", paginate_by=None
):
    """
    Render a list of items

    Usage example::

        def article_list(request, ...):
            queryset = Article.objects.published()
            return render_list(
                request,
                queryset,
                paginate_by=10,
            )

    You can also pass an additional context dictionary and/or specify the
    template name suffix. The query parameter ``page`` is hardcoded for
    specifying the current page if using pagination.

    The queryset (or the page if using pagination) are passed into the template
    as ``object_list`` AND ``<model_name>_list``, i.e. ``article_list`` in the
    example above.
    """

    context = context or {}
    if paginate_by:
        p = paginator.Paginator(queryset, paginate_by)
        # Note! Django>=2.0 allows us to simply
        # object_list = p.get_page(request.GET.get("page"))
        try:
            object_list = p.page(request.GET.get("page"))
        except paginator.PageNotAnInteger:
            object_list = p.page(1)
        except paginator.EmptyPage:
            object_list = p.page(p.num_pages)
    else:
        object_list = queryset

    context.update(
        {
            "object_list": object_list,
            "%s_list" % queryset.model._meta.model_name: object_list,
        }
    )
    return TemplateResponse(
        request, template_name(queryset.model, template_name_suffix), context
    )


def render_detail(request, object, context=None, *, template_name_suffix="_detail"):
    """
    Render a single item

    Usage example::

        def article_detail(request, slug):
            article = get_object_or_404(Article.objects.published(), slug=slug)
            return render_detail(
                request,
                article,
            )

    An additional context dictionary is also supported, and specifying the
    template name suffix too.

    The ``Article`` instance in the example above is passed as ``object``
    AND ``article`` (lowercased model name) into the template.
    """

    context = context or {}
    context.update({"object": object, object._meta.model_name: object})
    return TemplateResponse(
        request, template_name(object, template_name_suffix), context
    )
