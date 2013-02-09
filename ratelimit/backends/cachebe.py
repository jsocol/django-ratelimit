import hashlib

from django.core.cache import get_cache

from ratelimit.backends import BaseBackend


CACHE_PREFIX = 'rl:'


class CacheBackend(BaseBackend):
    def _keys(self, request, ip=True, field=None):
        keys = []
        if ip:
            keys.append('ip:' + request.META['REMOTE_ADDR'])
        if field is not None:
            if not isinstance(field, (list, tuple)):
                field = [field]
            for f in field:
                val = getattr(request, request.method).get(f, '').encode('utf-8')
                # Convert value to hexdigest as cache backend doesn't allow
                # certain characters.
                val = hashlib.sha1(val).hexdigest()
                keys.append(u'field:%s:%s' % (f, val))
        return [CACHE_PREFIX + k for k in keys]

    def count(self, request, ip=True, field=None, period=60, use='default'):
        counters = dict((key, 0) for key in self._keys(request, ip, field))
        mycache = get_cache(use)
        counters.update(mycache.get_many(counters.keys()))
        for key in counters:
            counters[key] += 1
        mycache.set_many(counters, timeout=period)

    def limit(self, request, ip=True, field=None, count=5, use='default'):
        counters = get_cache(use).get_many(self._keys(request, ip, field))
        return any((v > count) for v in counters.values())
