import os

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


MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'feincms3.apps.AppsMiddleware',
]

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'format_tags': 'h1;h2;h3;p;pre',
        'toolbar_Custom': [
            ['Format', 'RemoveFormat'],
            ['Bold', 'Italic', 'Strike', '-',
             'NumberedList', 'BulletedList', '-',
             'Anchor', 'Link', 'Unlink', '-',
             'Source'],
        ],
    },
}

# Settings for feincms3.plugins.richtext.RichText
CKEDITOR_CONFIGS['richtext-plugin'] = CKEDITOR_CONFIGS['default']
