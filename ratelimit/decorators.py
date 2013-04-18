import re
from functools import wraps

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

from django.utils.importlib import import_module
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
    t = _PERIODS[period.lower()]
    if multi:
        t = t * int(multi)
    return count, t


def ratelimit(ip=True, block=False, method=['POST'], field=None, rate='5/m',
              skip_if=None, keys=None, warning=None, backend="cache"):
    def decorator(fn):
        count, period = _split_rate(rate)

        @wraps(fn)
        def _wrapped(request, *args, **kw):
            b = _get_backend(backend)

            request.limited = False
            if (RATELIMIT_ENABLE and _method_match(request, method) and
                    (skip_if is None or not skip_if(request))):
                _keys = b._get_keys(request, ip, field, keys)
                counts = b._incr(_keys, period)
                logger.debug(counts)
                # additional info added to the request
                # usefull go get a warning when an ip is almost throttled
                if ip and warning is not None:
                    ip_key = CACHE_PREFIX + "ip:" + request.META['REMOTE_ADDR']
                    if ip_key in counts:
                        request.throttled_count_ip = (counts[ip_key], count, warning)

                if any([c > count for c in counts.values()]):
                    request.limited = True
                    if block:
                        raise Ratelimited()

            return fn(request, *args, **kw)
        return _wrapped
    return decorator


def _get_backend(backend):
    module = 'ratelimit.backends.%s.%sRateLimitBackend' % (backend, backend.title())
    parts = module.split('.')
    modname = '.'.join(parts[:-1])
    clsname = parts[-1]
    logger.debug(modname)
    mod = import_module(modname)
    cls = getattr(mod, clsname)
    return cls()
