SECRET_KEY = 'ratelimit'

INSTALLED_APPS = (
    'ratelimit',
)

RATELIMIT_USE_CACHE = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-tests',
    },
    'connection-errors': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
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

# silence system check about unset `MIDDLEWARE_CLASSES`
SILENCED_SYSTEM_CHECKS = ['1_7.W001']
