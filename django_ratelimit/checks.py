from django.conf import settings
from django.core import checks

SUPPORTED_CACHE_BACKENDS = [
    'django.core.cache.backends.memcached.PyMemcacheCache',
    'django.core.cache.backends.memcached.PyLibMCCache',
    'django_redis.cache.RedisCache',
]

CACHE_FAKE = 'is not a real cache'
CACHE_NOT_SHARED = 'is not a shared cache'
CACHE_NOT_ATOMIC = 'does not support atomic increment'

KNOWN_BROKEN_CACHE_BACKENDS = {
    'django.core.cache.backends.dummy.DummyCache': CACHE_FAKE,
    'django.core.cache.backends.locmem.LocMemCache': CACHE_NOT_SHARED,
    'django.core.cache.backends.filebased.FileBasedCache': CACHE_NOT_ATOMIC,
    'django.core.cache.backends.db.DatabaseCache': CACHE_NOT_ATOMIC,
}


@checks.register(checks.Tags.caches, 'django_ratelimit')
def check_caches(app_configs, **kwargs):
    errors = []
    cache_name = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    caches = getattr(settings, 'CACHES', None)
    if caches is None:
        errors.append(
            checks.Error(
                'CACHES is not defined, django_ratelimit will not work',
                hint='Configure a default cache using memcached or redis.',
                id='django_ratelimit.E001',
            )
        )
        return errors

    if cache_name not in caches:
        errors.append(
            checks.Error(
                f'RATELIMIT_USE_CACHE value "{cache_name}"" does not '
                f'appear in CACHES dictionary',
                hint='RATELIMIT_USE_CACHE must be set to a valid cache',
                id='django_ratelimit.E002',
            )
        )
        return errors

    cache_config = caches[cache_name]
    backend = cache_config['BACKEND']

    reason = KNOWN_BROKEN_CACHE_BACKENDS.get(backend, None)
    if reason is not None:
        errors.append(
            checks.Error(
                f'cache backend {backend} {reason}',
                hint='Use a supported cache backend',
                id='django_ratelimit.E003',
            )
        )

    if backend not in SUPPORTED_CACHE_BACKENDS:
        errors.append(
            checks.Warning(
                f'cache backend {backend} is not officially supported',
                id='django_ratelimit.W001',
            )
        )

    return errors
