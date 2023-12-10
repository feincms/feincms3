from django.db import models
from django.db.models.query import ModelIterable
from django.utils.translation import gettext_lazy as _


class ProxyModelIterable(ModelIterable):
    def __iter__(self):
        for obj in super().__iter__():
            obj.__class__ = obj._proxy_model_registry[obj.type]
            yield obj


class ProxyManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset._iterable_class = ProxyModelIterable
        return queryset


class ProxyModelBase(models.Model):
    type = models.CharField(_("type"), max_length=1000, editable=False)

    objects = ProxyManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.type = self.TYPE
        super().save(*args, **kwargs)

    save.alters_data = True

    @classmethod
    def proxy(cls, type_name, *, attrs=None, **meta):
        meta["proxy"] = True
        meta["app_label"] = cls._meta.app_label
        meta.setdefault("verbose_name", type_name)

        meta_class = type("Meta", (cls.Meta,), meta)

        if attrs is None:
            attrs = {}
        attrs |= {
            "__module__": cls.__module__,
            "Meta": meta_class,
            "TYPE": type_name,
        }
        if not hasattr(cls, "_proxy_model_registry"):
            cls._proxy_model_registry = {}
        proxy = type(f"{cls.__qualname__}_{type_name}", (cls,), attrs)
        cls._proxy_model_registry[type_name] = proxy
        return proxy
