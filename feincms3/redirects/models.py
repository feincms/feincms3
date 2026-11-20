from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import DisallowedHost
from django.db import models
from django.http.request import split_domain_port
from django.urls import NoReverseMatch
from django.utils.translation import gettext_lazy as _

from feincms3.redirects import registration
from feincms3.utils import validation_error


def _url(instance):
    try:
        return instance.get_absolute_url()
    except NoReverseMatch:
        return None


def _request_hosts(request):
    try:
        host = request.get_host().lower()
    except DisallowedHost:
        return [""]
    domain, _port = split_domain_port(host)
    return list(dict.fromkeys([host, domain, ""]))


class RedirectQuerySet(models.QuerySet):
    def record(self, instance):
        """
        Record the current URL of a registered instance
        """
        if not (reg := registration(instance)) or not (url := _url(instance)):
            return
        parts = urlsplit(url)
        host = reg.get_host(instance) if reg.get_host else parts.netloc
        values = {
            "content_type": ContentType.objects.get_for_model(instance),
            "object_id": str(instance.pk),
            "target_url": "",
            "is_automatic": True,
            "permanent": True,
        }
        # A single upsert query; also takes over rows of other objects or
        # manual redirects, since the instance serves the URL now.
        self.bulk_create(
            [self.model(host=(host or "").lower(), path=unquote(parts.path), **values)],
            update_conflicts=True,
            unique_fields=["host", "path"],
            update_fields=list(values),
        )

    def find(self, request):
        """
        Return a ``(url, permanent)`` tuple for the redirect matching the
        request, or ``None``
        """
        path = request.path
        paths = [path]
        if settings.APPEND_SLASH and not path.endswith("/"):
            paths.append(f"{path}/")
        query = request.META.get("QUERY_STRING", "")
        candidates = ([f"{p}?{query}" for p in paths] + paths) if query else paths
        hosts = _request_hosts(request)

        rows = sorted(
            self.filter(host__in=hosts, path__in=candidates),
            key=lambda row: (candidates.index(row.path), hosts.index(row.host)),
        )
        for row in rows:
            if not (url := row.resolve(request)):
                continue
            parts = urlsplit(url)
            if unquote(parts.path) == path and parts.netloc.lower() in hosts:
                # The target is the current URL, do not redirect to self.
                continue
            if query and "?" not in row.path:
                url = f"{url}{'&' if parts.query else '?'}{query}"
            return url, row.permanent
        return None


class Redirect(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    host = models.CharField(
        _("host"),
        max_length=255,
        blank=True,
        help_text=_("Leave empty to redirect requests to all hosts."),
    )
    path = models.CharField(
        _("path"),
        max_length=1000,
        help_text=_(
            "The path, starting with a slash and excluding the host. May"
            " contain a query string, e.g. '/index.php?id=12'."
        ),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("content type"),
    )
    object_id = models.CharField(_("object ID"), max_length=255, blank=True)
    target_object = GenericForeignKey("content_type", "object_id")
    target_url = models.CharField(
        _("target URL"),
        max_length=1000,
        blank=True,
        help_text=_("An absolute path or a full URL."),
    )
    is_automatic = models.BooleanField(
        _("is automatic"),
        default=False,
        help_text=_("Recorded automatically when saving the target object."),
    )
    permanent = models.BooleanField(_("permanent"), default=True)

    objects = RedirectQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["host", "path"], name="feincms3_redirects_unique_path"
            ),
        ]
        indexes = [models.Index(fields=["content_type", "object_id"])]
        ordering = ["host", "path"]
        verbose_name = _("redirect")
        verbose_name_plural = _("redirects")

    def __str__(self):
        return f"{self.host}{self.path}"

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        self.host = self.host.lower()
        if not self.path.startswith("/"):
            raise validation_error(
                _("The path must start with a slash."), field="path", exclude=exclude
            )
        # Paths are matched against the decoded request.path, query strings
        # against the undecoded QUERY_STRING.
        path, sep, query = self.path.partition("?")
        self.path = f"{unquote(path)}{sep}{query}"

        has_object = bool(self.content_type_id or self.object_id)
        if bool(self.target_url) == has_object:
            raise validation_error(
                _("Set either a target URL or a target object."),
                field="target_url",
                exclude=exclude,
            )
        if has_object:
            model = self.content_type and self.content_type.model_class()
            if not model or not registration(model):
                raise validation_error(
                    _("Objects of this type cannot be redirected to."),
                    field="content_type",
                    exclude=exclude,
                )
            if not model._default_manager.filter(pk=self.object_id).exists():
                raise validation_error(
                    _("The target object does not exist."),
                    field="object_id",
                    exclude=exclude,
                )

    def get_target_url(self):
        """
        Return the URL of the redirect's target, without checking the
        registration's queryset; used in the admin
        """
        if self.target_url:
            return self.target_url
        return (obj := self.target_object) and _url(obj)

    def resolve(self, request):
        """
        Return the URL of the redirect's target, or ``None`` if the target
        doesn't exist or isn't contained in the registration's queryset
        """
        if self.target_url:
            return self.target_url
        if not self.content_type_id:
            return None
        model = ContentType.objects.get_for_id(self.content_type_id).model_class()
        if model is None or not (reg := registration(model)):
            return None
        instance = reg.get_queryset(request).filter(pk=self.object_id).first()
        return instance and _url(instance)
