import os
import warnings

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'feincms3',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'testapp',

    # Libraries
    'feincms3',
    'content_editor',

    # Libraries for content-editor plugins
    'ckeditor',
    'versatileimagefield',
]

MEDIA_ROOT = '/media/'
STATIC_URL = '/static/'
BASEDIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASEDIR, 'media/')
STATIC_ROOT = os.path.join(BASEDIR, 'static/')
SECRET_KEY = 'supersikret'
LOGIN_REDIRECT_URL = '/?login=1'

ROOT_URLCONF = 'testapp.urls'
LANGUAGES = (('en', 'English'), ('de', 'German'))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'feincms3.apps.AppsMiddleware',
]
# Do not warn about MIDDLEWARE_CLASSES
SILENCED_SYSTEM_CHECKS = ['1_10.W001']

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'format_tags': 'h1;h2;h3;p;pre',
        'toolbar_Custom': [
            ['Format', 'RemoveFormat'],
            ['Bold', 'Italic', '-',
             'NumberedList', 'BulletedList', '-',
             'Anchor', 'Link', 'Unlink', '-',
             'Source'],
        ],
    },
}

# Settings for feincms3.plugins.richtext.RichText
CKEDITOR_CONFIGS['richtext-plugin'] = CKEDITOR_CONFIGS['default']


# Something about inspect.getargspec in beautifulsoup4.
warnings.filterwarnings(
    'ignore',
    module=r'bs4\.builder\._lxml')

try:
    # We do not yet care about those.
    from django.utils.deprecation import RemovedInDjango21Warning

    warnings.simplefilter('ignore', RemovedInDjango21Warning)
except ImportError:  # pragma: no cover
    pass
