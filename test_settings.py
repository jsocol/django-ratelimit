SECRET_KEY = 'ratelimit'

SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']

INSTALLED_APPS = (
    'django_ratelimit',
    'rest_framework',
)

RATELIMIT_USE_CACHE = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-tests',
    },
    'connection-errors': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': 'test-connection-errors',
    },
    'connection-errors-redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://test-connection-errors',
        'OPTIONS': {
            'IGNORE_EXCEPTIONS': True,
        }
    },
    'instant-expiration': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'test-instant-expiration',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}

USE_TZ = True
