import re
from functools import wraps

from django.http import HttpResponseForbidden
from django.conf import settings

from ratelimit.backends.cachebe import CacheBackend

RATELIMIT_DISABLE_ALL = getattr(settings, 'RATELIMIT_DISABLE_ALL', False)

def _method_match(request, method=None):
    if method is None:
        method = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
    if not isinstance(method, list):
        method = [method]
    return request.method in method


_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

rate_re = re.compile('([\d]+)/([\d]*)([smhd])')


def _split_rate(rate):
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    time = _PERIODS[period.lower()]
    if multi:
        time = time * int(multi)
    return count, time


_backend = CacheBackend()


def ratelimit(ip=True, block=False, method=None, field=None, rate='5/m', skip_if=None):
    def decorator(fn):
        count, period = _split_rate(rate)

        @wraps(fn)
        def _wrapped(request, *args, **kw):
            if _method_match(request, method) and not RATELIMIT_DISABLE_ALL:
                _backend.count(request, ip, field, period)
                if _backend.limit(request, ip, field, count):
                    if skip_if is None or (skip_if and not skip_if(request)):
                        if block:
                            return HttpResponseForbidden()
                        request.limited = True
            return fn(request, *args, **kw)
        return _wrapped
    return decorator
