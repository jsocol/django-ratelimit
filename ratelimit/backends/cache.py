import hashlib

from django.conf import settings
from django.core.cache import get_cache

from ratelimit.backends import RateLimitBackend

__all__ = ['CacheBackend']

CACHE_PREFIX = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')


class CacheBackend(RateLimitBackend):
    """ Rate limit backend that uses Django's cache """

    def __init__(self):
        cache = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
        self.cache = get_cache(cache)


    def _incr(self, keys, timeout=60):
        # Yes, this is a race condition, but memcached.incr doesn't reset the
        # timeout.
        keys = [CACHE_PREFIX + k for k in keys]
        counts = self.cache.get_many(keys)
        for key in keys:
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1
        self.cache.set_many(counts, timeout=timeout)
        return counts


    def hit(self, request, ip, field, keys, period):
        _keys = self._get_keys(request, ip, field, keys)
        counts = self._incr(_keys, period)
        return counts
