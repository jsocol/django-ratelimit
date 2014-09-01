import hashlib
import re
import time
import zlib

from django.conf import settings
from django.core.cache import get_cache
from django.core.excpetions import ImproperlyConfigured


__all__ = ['is_ratelimited']

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}


def user_or_ip(request):
    if request.user.is_authenticated():
        return str(request.user.pk)
    return request.META['REMOTE_ADDR']


_SIMPLE_KEYS = {
    'ip': lambda r: r.META['REMOTE_ADDR'],
    'user': lambda r: str(r.user.pk),
    'user_or_ip': user_or_ip,
}


def get_header(request, header):
    key = 'HTTP_' + header.replace('-', '_').upper()
    return request.META[key]


_ACCESSOR_KEYS = {
    'get': lambda r, k: r.GET[k],
    'post': lambda r, k: r.POST[k],
    'field': lambda r, k: r.POST[k] if request.method == 'POST' else r.GET[k],
    'header': get_header,
}

rate_re = re.compile('([\d]+)/([\d]*)([smhd])')


def _method_match(request, method=None):
    if method is None:
        return True
    if not isinstance(method, (list, tuple)):
        method = [method]
    return request.method in [m.upper() for m in method]


def _split_rate(rate):
    if isinstance(rate, tuple):
        return rate
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    time = _PERIODS[period.lower()]
    if multi:
        time = time * int(multi)
    return count, time


def _get_window(value, period):
    ts = int(time.time())
    if period == 1:
        return ts
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(group, rate, value):
    count, period = _split_rate(rate)
    window = _get_window(value, period)
    safe_rate = '%d/%ds' % (count, period)
    m = md5(group + safe_rate, value, str(window))
    return settings.RATELIMIT_CACHE_PREFIX + m.hexdigest()


def is_ratelimited(request, group=None, key=None, rate=None, method='POST',
                   increment=False):
    if not settings.RATELIMIT_ENABLE_CACHE:
        request.limited = False
        return False

    old_limited = getattr(request, 'limited', False)

    if callable(rate):
        rate = rate(group, request)

    if rate is None:
        request.limited = old_limited
        return False

    limit, period = _split_rate(rate)

    cache = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    # TODO: Django 1.7+
    cache = get_cache(cache)

    if callable(key):
        value = key(request)
    elif key in _SIMPLE_KEYS:
        value = _SIMPLE_KEYS[key](request)
    elif ':' in key:
        accessor, k = key.split(':', 1)
        if accessor not in _ACCESSOR_KEYS:
            raise ImproperlyConfigured('Unknown ratelimit key: %s' % key)
        value = _ACCESSOR_KEYS[accessor](request, k)
    else:
        # TODO: import path

    cache_key = _make_cache_key(group, rate, value)
    if increment:
        count = cache.incr(cache_key)
    else:
        count = cache.get(cache_key)
    limited = count > limit
    if increment:
        request.limited = old_limited or limited
    return limited
