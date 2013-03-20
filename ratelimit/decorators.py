import hashlib
import re
from functools import wraps

from django.conf import settings
from django.core.cache import get_cache

from ratelimit.exceptions import Ratelimited


__all__ = ['ratelimit']

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


def _get_keys(request, ip=True, field=None):
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


def ratelimit(ip=True, block=False, method=['POST'], field=None, rate='5/m',
              skip_if=None):
    def decorator(fn):
        count, period = _split_rate(rate)

        @wraps(fn)
        def _wrapped(request, *args, **kw):
            cache = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
            cache = get_cache(cache)

            request.limited = False
            if (RATELIMIT_ENABLE and _method_match(request, method) and
                    (skip_if is None or not skip_if(request))):
                counts = _incr(cache, _get_keys(request, ip, field), period)
                if any([c > count for c in counts.values()]):
                    request.limited = True
                    if block:
                        raise Ratelimited()

            return fn(request, *args, **kw)
        return _wrapped
    return decorator
