from django.conf import settings
from django.core.cache import get_cache

from ratelimit.backends import RateLimitBackend
from ratelimit.exceptions import InvalidConfig

from django.core.cache import InvalidCacheBackendError

__all__ = ['CacheRateLimitBackend']

CACHE_PREFIX = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')


class CacheRateLimitBackend(RateLimitBackend):
    def __init__(self):
        cache = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
        try:
            self.cache = get_cache(cache)
        except InvalidCacheBackendError:
            raise InvalidConfig

    def _incr(self, keys, timeout=60):
        # Yes, this is a race condition, but memcached.incr doesn't reset the
        # timeout.
        counts = self.cache.get_many(keys)
        for key in keys:
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1
        self.cache.set_many(counts, timeout=timeout)
        return counts
