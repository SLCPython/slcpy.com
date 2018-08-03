import os

import dj_database_url

from decouple import config, Csv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = os.path.realpath(os.path.join(BASE_DIR, '..'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    'SECRET_KEY',
    default='zs$zd9my5&ob&v56s=!3s1#rbk(%rajxbkrjtbsz1+&)9*k-7b')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS',
                       default='localhost', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # sentry
    'raven.contrib.django.raven_compat',

    'slcpy.users',
    'slcpy.home'
]
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'slcpy.urls'

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

WSGI_APPLICATION = 'slcpy.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DEFAULT_DATABASE = config(
    'DATABASE_URL',
    default='postgres://cramstack:cramstack@localhost:5432/cramstack',
    cast=dj_database_url.parse)

DATABASES = {
    'default': DEFAULT_DATABASE
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

MEDIA_DIR = os.path.realpath(os.path.join(HOME_DIR, 'media/'))

MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

AUTH_USER_MODEL = 'users.User'

# Config to make the registration email only
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
# Sentry configuration
RAVEN_CONFIG = {
    'dsn': config('SENTRY_DSN_URL', default=None),
}
