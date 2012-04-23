import hashlib

from django.core.cache import cache
from django.core.cache.backends.base import BaseCache

from ratelimit.backends import BaseBackend


CACHE_PREFIX = 'rl:'
BASE_CACHE = BaseCache({})
IP_PREFIX = 'ip:'
IP_TPL = '%s%s:%s%s'
PERIOD_PREFIX = 'period:'


class CacheBackend(BaseBackend):
    def _keys(self, request, ip=True, field=None, period=None):
        keys = []
        meta = request.META
        if ip:
            if 'HTTP_TRUE_CLIENT_IP' in meta:
                # If Akamai routes requests to you:
                keys.append(IP_TPL % (
                    PERIOD_PREFIX, period,
                    IP_PREFIX, meta['HTTP_TRUE_CLIENT_IP']
                ))
            elif 'HTTP_X_FORWARDED_FOR' in meta:
                # For any other proxy or load balancer:
                # The first element is the original IP.
                keys.append(IP_TPL % (
                    PERIOD_PREFIX, period,
                    IP_PREFIX, meta['HTTP_X_FORWARDED_FOR'].split(',')[0]
                ))
            else:
                keys.append(IP_TPL % (
                    PERIOD_PREFIX, period,
                    IP_PREFIX, meta['REMOTE_ADDR']
                ))

        if field is not None:
            if not isinstance(field, (list, tuple)):
                field = [field]
            for f in field:
                val = getattr(request, request.method).get(f)
                # Convert value to hexdigest as cache backend doesn't allow
                # certain characters
                if val:
                    val = hashlib.sha1(val).hexdigest()
                    keys.append('%s%s:field:%s:%s' % (
                        PERIOD_PREFIX, period,
                        f, val
                    ))

        return [
            BASE_CACHE.make_key(CACHE_PREFIX + k) for k in keys
        ]

    def count(self, request, ip=True, field=None, period=60):
        counters = dict((key, 0) for key in self._keys(
            request, ip, field, period))
        counters.update(cache.get_many(counters.keys()))
        for key in counters:
            counters[key] += 1
        cache.set_many(counters, timeout=period)

    def limit(self, request, ip=True, field=None, count=5, period=None):
        counters = cache.get_many(self._keys(request, ip, field, period))
        return any((v > count) for v in counters.values())
