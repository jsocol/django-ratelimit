from django.core.cache import cache

from ratelimit.backends import BaseBackend


CACHE_PREFIX = 'rl:'


class CacheBackend(BaseBackend):
    def _keys(self, request, ip=True, field=None):
        keys = []
        if ip:
            keys.append('ip:' + request.META['REMOTE_ADDR'])
        if not field is None:
            if not isinstance(field, list):
                field = [field]
            for f in field:
                keys.append('field:' + f)
        return keys

    def count(self, request, ip=True, field=None):
        for key in self._keys(request, ip, field):
            curr = cache.get(key, 0)
                cache.set(key, curr + 1, 60)

    def limit(self, request, ip=True, field=None, rate=5):
        for key in self._keys(request, ip, field):
            if cache.get(key, 0) > rate:
                return True
        return False
