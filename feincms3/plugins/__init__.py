# flake8: noqa

from feincms3.plugins import html, snippet


try:
    import html_sanitizer
except ImportError:  # pragma: no cover
    pass
else:
    from feincms3.plugins import richtext
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
try:
    import ckeditor
except ImportError:  # pragma: no cover
    pass
else:
    from feincms3.plugins import old_richtext
