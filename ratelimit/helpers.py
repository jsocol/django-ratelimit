import hashlib
import re

from django.conf import settings
from django.core.cache import get_cache


__all__ = ['is_ratelimited']

RATELIMIT_ENABLE = getattr(settings, 'RATELIMIT_ENABLE', True)
CACHE_PREFIX = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

rate_re = re.compile('([\d]+)/([\d]*)([smhd])')


def _method_match(request, method=None):
    if method is None:
        return True
    if not isinstance(method, (list, tuple)):
        method = [method]
    return request.method in [m.upper() for m in method]


def _split_rate(rate):
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    time = _PERIODS[period.lower()]
    if multi:
        time = time * int(multi)
    return count, time


def _get_keys(request, ip=True, field=None, keyfuncs=None):
    keys = []
    if ip:
        keys.append('ip:' + request.META['REMOTE_ADDR'])
    if field is not None:
        if not isinstance(field, (list, tuple)):
            field = [field]
        for f in field:
            val = getattr(request, request.method).get(f, '').encode('utf-8')
            val = hashlib.sha1(val).hexdigest()
            keys.append(u'field:%s:%s' % (f, val))
    if keyfuncs:
        if not isinstance(keyfuncs, (list, tuple)):
            keyfuncs = [keyfuncs]
        for k in keyfuncs:
            keys.append(k(request))
    return [CACHE_PREFIX + k for k in keys]


def _incr(cache, keys, timeout=60):
    # Yes, this is a race condition, but memcached.incr doesn't reset the
    # timeout.
    counts = cache.get_many(keys)
    for key in keys:
        if key in counts:
            counts[key] += 1
        else:
            counts[key] = 1
    cache.set_many(counts, timeout=timeout)
    return counts

def _get(cache, keys):
    counts = cache.get_many(keys)
    for key in keys:
        if key in counts:
            counts[key] += 1
        else:
            counts[key] = 1
    return counts


def is_ratelimited(request, increment=False, ip=True, method=['POST'],
                   field=None, rate='5/m', keys=None):
    count, period = _split_rate(rate)
    cache = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    cache = get_cache(cache)

    request.limited = getattr(request, 'limited', False)
    if (not request.limited and RATELIMIT_ENABLE and
            _method_match(request, method)):
        _keys = _get_keys(request, ip, field, keys)
        if increment:
            counts = _incr(cache, _keys, period)
        else:
            counts = _get(cache, _keys)
        if any([c > count for c in counts.values()]):
            request.limited = True

    return request.limited
