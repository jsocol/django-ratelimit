import hashlib

from django.core.cache import cache

from ratelimit.backends import BaseBackend


CACHE_PREFIX = 'rl:'


class CacheBackend(BaseBackend):

    def key_transform(self, request, key_funcs):
        keys = super(CacheBackend, self).key_transform(request, key_funcs)

        def trans(key):
            """Convert value to hexdigest as cache backend doesn't allow
            certain characters."""
            return CACHE_PREFIX + hashlib.sha1(key).hexdigest().encode('utf-8')

        keys = [trans(k) for k in keys]
        return keys

    def count(self, request, keys, period):
        counters = dict((key, 0) for key in self.key_transform(request, keys))
        counters.update(cache.get_many(counters.keys()))
        for key in counters:
            counters[key] += 1
        cache.set_many(counters, timeout=period)

    def limit(self, request, keys, count):
        counters = cache.get_many(self.key_transform(request, keys))
        return any((v > count) for v in counters.values())
