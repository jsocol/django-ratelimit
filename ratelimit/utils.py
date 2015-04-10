import hashlib
import re
import time
import zlib

from django.conf import settings
from django.core.cache import get_cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from ratelimit import ALL, UNSAFE


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
    'get': lambda r, k: r.GET.get(k, ''),
    'post': lambda r, k: r.POST.get(k, ''),
    'header': get_header,
}


def _method_match(request, method=ALL):
    if method == ALL:
        return True
    if not isinstance(method, (list, tuple)):
        method = [method]
    return request.method in [m.upper() for m in method]


rate_re = re.compile('([\d]+)/([\d]*)([smhd])?')


def _split_rate(rate):
    if isinstance(rate, tuple):
        return rate
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    if not period:
        period = 's'
    seconds = _PERIODS[period.lower()]
    if multi:
        seconds = seconds * int(multi)
    return count, seconds


def _get_window(value, period):
    ts = int(time.time())
    if period == 1:
        return ts
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(group, rate, value, methods):
    count, period = _split_rate(rate)
    safe_rate = '%d/%ds' % (count, period)
    window = _get_window(value, period)
    parts = [group + safe_rate, value, str(window)]
    if methods is not None:
        if methods == ALL:
            methods = ''
        elif isinstance(methods, (list, tuple)):
            methods = ''.join(sorted([m.upper() for m in methods]))
        parts.append(methods)
    prefix = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')
    return prefix + hashlib.md5(u''.join(parts).encode('utf-8')).hexdigest()


def _prepare_rate(rate, group, request):
    if callable(rate):
        rate = rate(group, request)
    return rate


def get_ratelimit_cache():
    cache_name = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    # TODO: Django 1.7+
    cache = get_cache(cache_name)
    return cache


def get_cache_key_for_request(request, group=None, fn=None, key=None,
                              rate=None, method=ALL):
    if not key:
        raise ImproperlyConfigured('Ratelimit key must be specified')
    if group is None:
        if hasattr(fn, '__self__'):
            parts = fn.__module__, fn.__self__.__class__.__name__, fn.__name__
        else:
            parts = (fn.__module__, fn.__name__)
        group = '.'.join(parts)

    rate = _prepare_rate(rate, group, request)

    if callable(key):
        value = key(group, request)
    elif key in _SIMPLE_KEYS:
        value = _SIMPLE_KEYS[key](request)
    elif ':' in key:
        accessor, k = key.split(':', 1)
        if accessor not in _ACCESSOR_KEYS:
            raise ImproperlyConfigured('Unknown ratelimit key: %s' % key)
        value = _ACCESSOR_KEYS[accessor](request, k)
    elif '.' in key:
        mod, attr = key.rsplit('.', 1)
        keyfn = getattr(import_module(mod), attr)
        value = keyfn(group, request)
    else:
        raise ImproperlyConfigured(
            'Could not understand ratelimit key: %s' % key)

    return _make_cache_key(group, rate, value, method)


def is_ratelimited(request, group=None, fn=None, key=None, rate=None,
                   method=ALL, increment=False):
    if not key:
        raise ImproperlyConfigured('Ratelimit key must be specified')
    if not getattr(settings, 'RATELIMIT_ENABLE', True):
        request.limited = False
        return False

    if not _method_match(request, method):
        return False

    old_limited = getattr(request, 'limited', False)

    rate = _prepare_rate(rate, group, request)
    if rate is None:
        request.limited = old_limited
        return False
    limit, period = _split_rate(rate)

    cache = get_ratelimit_cache()
    cache_key = get_cache_key_for_request(
        request, group, fn, key, rate, method,
    )

    cache.add(cache_key, 0)
    if increment:
        try:
            count = cache.incr(cache_key)
        except ValueError:
            # key already expired or removed because we lack memory
            count = 1
    else:
        count = cache.get(cache_key)
    limited = count > limit
    if increment:
        request.limited = old_limited or limited
    return limited


is_ratelimited.ALL = ALL
is_ratelimited.UNSAFE = UNSAFE
