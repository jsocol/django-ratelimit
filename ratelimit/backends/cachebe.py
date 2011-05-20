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
                val = getattr(request, request.method).get(f)
                keys.append(u'field:%s:%s' % (f, val))
        return [CACHE_PREFIX + k for k in keys]

    def count(self, request, ip=True, field=None, period=60):
        for key in self._keys(request, ip, field):
            curr = cache.get(key, 0)
            cache.set(key, curr + 1, period)

    def limit(self, request, ip=True, field=None, count=5):
        for key in self._keys(request, ip, field):
            if cache.get(key, 0) > count:
                return True
        return False
