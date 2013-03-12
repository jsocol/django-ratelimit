import hashlib

from django.core.cache import cache

from ratelimit.backends import BaseBackend


CACHE_PREFIX = 'rl:'


class CacheBackend(BaseBackend):

    def key_transform(self, request, key_funcs):
        keys = super(CacheBackend, self).key_transform(request, key_funcs)

        def trans(key):
            # Memcached can't handle some kinds of characters, like Non-
            # ASCII characters or control characters. Since this key is
            # probably going to memcached, conform to it. SHA1 hashes
            # encoded as hexadecimal matches all of Memcached's
            # requirements. Hashlib only works on encoded byte strings.
            return CACHE_PREFIX + hashlib.sha1(key.encode('utf-8')).hexdigest()

        return [trans(k) for k in keys]

    def count(self, request, keys, period):
        counters = dict((key, 0) for key in self.key_transform(request, keys))
        counters.update(cache.get_many(counters.keys()))
        for key in counters:
            counters[key] += 1
        cache.set_many(counters, timeout=period)

    def limit(self, request, keys, count):
        counters = cache.get_many(self.key_transform(request, keys))
        return any((v > count) for v in counters.values())
