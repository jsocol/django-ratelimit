import re
from functools import wraps

from django.conf import settings
from django.utils.importlib import import_module

from ratelimit.exceptions import Ratelimited


__all__ = ['ratelimit']

RATELIMIT_ENABLE = getattr(settings, 'RATELIMIT_ENABLE', True)

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


def _get_backend():
    """ Loads and instantiates the backendd

    The ``RATELIMIT_BACKEND`` setting must be set to the full name of the
    backend class.

    """
    RATELIMIT_BACKEND = getattr(settings, 'RATELIMIT_BACKEND',
                                'ratelimit.backends.cache.CacheBackend')

    parts = RATELIMIT_BACKEND.split('.')
    modname = '.'.join(parts[:-1])
    clsname = parts[-1]

    mod = import_module(modname)
    cls = getattr(mod, clsname)

    return cls()


def ratelimit(ip=True, block=False, method=['POST'], field=None, rate='5/m',
              skip_if=None, keys=None):
    def decorator(fn):
        count, period = _split_rate(rate)

        @wraps(fn)
        def _wrapped(request, *args, **kw):
            backend = _get_backend()

            request.limited = getattr(request, 'limited', False)
            if (not request.limited and RATELIMIT_ENABLE and
                    _method_match(request, method) and
                    (skip_if is None or not skip_if(request))):

                counts = backend.hit(request, ip, field, keys, period)
                if any([c > count for c in counts.values()]):
                    request.limited = True
                    if block:
                        raise Ratelimited()

            return fn(request, *args, **kw)
        return _wrapped
    return decorator
