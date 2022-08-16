import os

from scribble.settings import DB_NAME, DB_USER, DB_HOST, DB_PASSWORD, BASE_DIR, \
    ALLOWED_HOSTS as prod_env_hosts, \
    CORS_ORIGIN_WHITELIST as cors_origin_whitelist

from scribble.settings.base import INSTALLED_APPS

DEBUG = False

INSTALLED_APPS += [
    'corsheaders',
]

ALLOWED_HOSTS = prod_env_hosts

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': '5432'
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "token",
        "KEY_FUNCTION": "utils.cache.cache_key_function",
    }
}

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR.parent, 'app/static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR.parent, 'media')


CORS_ORIGIN_WHITELIST = cors_origin_whitelist

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE'
)

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)
