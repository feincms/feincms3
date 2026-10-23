import importlib

from feincms3.plugins import html, snippet


try:
    import requests
except ImportError:  # pragma: no cover
    pass
else:
    from feincms3.plugins import external
try:
    import imagefield
except ImportError:  # pragma: no cover
    pass
else:
    from feincms3.plugins import image


def __getattr__(name):
    # Deprecated plugins are only imported (and warn) when they are used
    if name in {"old_richtext", "richtext"}:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
