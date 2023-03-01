"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = ["localhost"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    'rest_framework.authtoken',
    "social_django",
    "users",
    "ai",
    "django_prometheus",
    "drf_spectacular",
    "django_extensions",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "main.middleware.SegmentMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "social_core.backends.github.GithubTeamOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "users.User"

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_ERROR_URL = 'login'

# To be updated with URL to pilot test plan
PILOT_DOCS_URL = os.environ.get(
    'PILOT_DOCS_URL', 'https://drive.google.com/drive/folders/1cyjv_Ljz9I2IXY140S7_fjQsqZtxr_sg'
)
PILOT_CONTACT = os.environ.get('PILOT_CONTACT', '#ansible-wisdom-pilot on Internal Red Hat Slack')

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_GITHUB_TEAM_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_TEAM_KEY')
SOCIAL_AUTH_GITHUB_TEAM_SECRET = os.environ.get('SOCIAL_AUTH_GITHUB_TEAM_SECRET')
SOCIAL_AUTH_GITHUB_TEAM_ID = os.environ.get('SOCIAL_AUTH_GITHUB_TEAM_ID', 7188893)
SOCIAL_AUTH_GITHUB_TEAM_SCOPE = ["read:org"]
# Wisdom Eng Team:
# gh api -H "Accept: application/vnd.github+json" /orgs/ansible/teams/wisdom-contrib

# Write key for sending analytics data to Segment. Note that each of Prod/Dev have a different key.
SEGMENT_WRITE_KEY = os.environ.get("SEGMENT_WRITE_KEY")

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.UserRateThrottle'],
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': ('users.auth.BearerTokenAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'  # comment out for unauthenticated API access
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


ROOT_URLCONF = "main.urls"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["ANSIBLE_AI_DATABASE_NAME"],
        "USER": os.environ["ANSIBLE_AI_DATABASE_USER"],
        "PASSWORD": os.environ["ANSIBLE_AI_DATABASE_PASSWORD"],
        "HOST": os.environ["ANSIBLE_AI_DATABASE_HOST"],
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Absolute filesystem path to the directory where static file are collected via
# the collectstatic command.
STATIC_ROOT = '/var/www/wisdom/public/static'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False

# Depending on how env var is set, can end up with extraneous quotes.
# this is defensive, we could just let it happen and
# leave it to the operator who set the var to fix it
COMPLETION_USER_RATE_THROTTLE = (
    os.environ.get('COMPLETION_USER_RATE_THROTTLE', '10/minute').strip('"').strip("'")
)

ENABLE_ARI_POSTPROCESS = os.getenv('ENABLE_ARI_POSTPROCESS', 'False').lower() == 'true'
ARI_BASE_DIR = os.getenv('ARI_KB_PATH', '/etc/ari/kb/')
ARI_RULES_DIR = os.path.join(ARI_BASE_DIR, 'rules')
ARI_DATA_DIR = os.path.join(ARI_BASE_DIR, 'data')
ARI_RULES = [
    "P001",
    "P002",
    "P003",
    "P004",
    "W001",
    "W003",
    "W004",
    "W005",
    "W006",
    "W007",
    "W008",
    "W009",
    "W010",
    "W012",
    "W013",
]
if 'ARI_RULES' in os.environ:
    ARI_RULES = os.environ['ARI_RULES'].split(',')
ARI_RULE_FOR_OUTPUT_RESULT = os.getenv('ARI_RULE_FOR_OUTPUT_RESULT', "W007")
