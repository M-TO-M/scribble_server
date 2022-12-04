import os
import json
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

from utils.logging_utils import Logger

load_dotenv()

VERSION = 'v1'

SECRET_KEY = os.environ.get('SECRET_KEY')

RUN_ENV = os.environ.get('RUN_ENV')
HOST_KEY = 'DEV_ALLOWED_HOSTS' if RUN_ENV == 'dev' else 'PROD_ALLOWED_HOSTS'
ALLOWED_HOSTS = json.loads(os.environ.get(HOST_KEY))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

NAVER_API_CLIENT_ID = os.environ.get('NAVER_API_CLIENT_ID')
NAVER_API_CLIENT_SECRET = os.environ.get('NAVER_API_CLIENT_SECRET')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'apps.users',
    'apps.contents',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_tracking',
    'drf_yasg',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'scribble.middleware.TokenAuthMiddleWare',
]

ROOT_URLCONF = 'scribble.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'scribble.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'utils.renderer.ResponseRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'scribble.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 6,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",

    "TOKEN_OBTAIN_SERIALIZER": "utils.serializers.ScribbleTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",

    "AUTH_COOKIE": "SCRIB_TOKEN",
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True
}

SWAGGER_SETTINGS = {
   'SECURITY_DEFINITIONS': {
      'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
      }
   }
}


LOG_DIR = os.environ.get('LOG_DIR')
LOG_FILENAME = os.environ.get('LOG_FILENAME')
os.makedirs(os.path.join(BASE_DIR, LOG_DIR), exist_ok=True)

scribble_logging_config = {
    "drivers": ["console", "file"],
    "level": "DEBUG",
    "handlers": {
        "console": {
            "level": "DEBUG",
            "format": "verbose",
            "filters": "django.utils.log.RequiredDebugTrue",
        },
        "file": {
            "level": "INFO",
            "path": os.path.join(BASE_DIR, LOG_DIR),
            "filename": LOG_FILENAME,
            "backup-count": 5,
            "rotation-size": 1024 * 1024 * 5,
        },
        "null": {"class": "logging.NullHandler", },
    },
    "packages": {"api": "INFO", "scribble": "INFO"}
}

logger = Logger(scribble_logging_config)


if RUN_ENV == "dev":
    INSTALLED_APPS += [
        'corsheaders',
    ]
    from .dev import *
else:
    from .prod import *
