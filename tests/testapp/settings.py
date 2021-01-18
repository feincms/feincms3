import os
import warnings


DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "testapp",
    # Libraries
    "feincms3",
    "content_editor",
    # Libraries for content-editor plugins
    "ckeditor",
    "imagefield",
]

MEDIA_URL = "/media/"
STATIC_URL = "/static/"
BASEDIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASEDIR, "media/")
STATIC_ROOT = os.path.join(BASEDIR, "static/")
SECRET_KEY = "supersikret"
LOGIN_REDIRECT_URL = "/?login=1"

ROOT_URLCONF = "testapp.urls"
LANGUAGES = [("en", "English"), ("de", "German"), ("fr", "French")]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

MIDDLEWARE = [
    "feincms3.applications.apps_middleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "format_tags": "h1;h2;h3;p;pre",
        "toolbar_Custom": [
            ["Format", "RemoveFormat"],
            [
                "Bold",
                "Italic",
                "-",
                "NumberedList",
                "BulletedList",
                "-",
                "Anchor",
                "Link",
                "Unlink",
                "-",
                "Source",
            ],
        ],
    }
}

# Settings for feincms3.plugins.richtext.RichText
CKEDITOR_CONFIGS["richtext-plugin"] = CKEDITOR_CONFIGS["default"]


def patch():
    # Monkey patch the translation module because versatileimagefield still
    # references those settings
    from django.utils import translation

    translation.ugettext = translation.gettext
    translation.ugettext_lazy = translation.gettext_lazy

    # Something about inspect.getargspec in beautifulsoup4.
    warnings.filterwarnings("ignore", module=r"bs4\.builder\._lxml")


patch()
