try:
    import pylibmc  # noqa: F401
    memcache_backend = "PyLibMCCache"
except ImportError:
    try:
        import pymemcache  # noqa: F401
        memcache_backend = "PyMemcacheCache"
    except ImportError:
        import memcache  # noqa: F401
        memcache_backend = "MemcachedCache"

SECRET_KEY = 'ratelimit'

INSTALLED_APPS = (
    'django_ratelimit',
)

RATELIMIT_USE_CACHE = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-tests',
    },
    'connection-errors': {
        'BACKEND': f'django.core.cache.backends.memcached.{memcache_backend}',
        'LOCATION': 'connection-errors',
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
