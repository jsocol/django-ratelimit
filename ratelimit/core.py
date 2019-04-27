import functools
import hashlib
import re
import time
import zlib

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from ratelimit import ALL, UNSAFE


__all__ = ['is_ratelimited', 'get_usage']

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

# Extend the expiration time by a few seconds to avoid misses.
EXPIRATION_FUDGE = 5


def user_or_ip(request):
    if request.user.is_authenticated:
        return str(request.user.pk)
    return request.META['REMOTE_ADDR']


_SIMPLE_KEYS = {
    'ip': lambda r: r.META['REMOTE_ADDR'],
    'user': lambda r: str(r.user.pk),
    'user_or_ip': user_or_ip,
}


def get_header(request, header):
    key = 'HTTP_' + header.replace('-', '_').upper()
    return request.META.get(key, '')


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


rate_re = re.compile(r'([\d]+)/([\d]*)([smhd])?')


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


def _make_cache_key(group, window, rate, value, methods):
    count, period = _split_rate(rate)
    safe_rate = '%d/%ds' % (count, period)
    parts = [safe_rate, value, str(window)]
    if methods is not None:
        if methods == ALL:
            methods = ''
        elif isinstance(methods, (list, tuple)):
            methods = ''.join(sorted([m.upper() for m in methods]))
        parts.append(methods)
    return "%(prefix)s:%(group)s:%(parts)s" % {
        "prefix": getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:'),
        "group": hashlib.md5(group.encode('utf-8')).hexdigest(),
        "parts": hashlib.new(
            getattr(settings, 'RATELIMIT_HASH_ALGORITHM', 'md5'),
            u''.join(parts).encode('utf-8')
        ).hexdigest()
    }


def is_ratelimited(request, group=None, fn=None, key=None, rate=None,
                   method=ALL, increment=False):
    usage = get_usage(request, group, fn, key, rate, method, increment)
    if usage is None:
        return False

    return usage['should_limit']


def get_usage(request, group=None, fn=None, key=None, rate=None, method=ALL,
              increment=False):
    if group is None and fn is None:
        raise ImproperlyConfigured('get_usage must be called with either '
                                   '`group` or `fn` arguments')

    if not getattr(settings, 'RATELIMIT_ENABLE', True):
        return None

    if not _method_match(request, method):
        return None

    if group is None:
        parts = []

        if isinstance(fn, functools.partial):
            fn = fn.func

        # Django <2.1 doesn't use a partial. This is ugly and inelegant, but
        # throwing __qualname__ into the list below helps.
        if fn.__name__ == 'bound_func':
            fn = fn.__closure__[0].cell_contents

        if hasattr(fn, '__module__'):
            parts.append(fn.__module__)

        if hasattr(fn, '__self__'):
            parts.append(fn.__self__.__class__.__name__)

        parts.append(fn.__qualname__)
        group = '.'.join(parts)

    if callable(rate):
        rate = rate(group, request)
    if rate is None:
        return None
    limit, period = _split_rate(rate)

    if not key:
        raise ImproperlyConfigured('Ratelimit key must be specified')
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
        keyfn = import_string(key)
        value = keyfn(group, request)
    else:
        raise ImproperlyConfigured(
            'Could not understand ratelimit key: %s' % key)

    window = _get_window(value, period)
    initial_value = 1 if increment else 0

    cache_name = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    cache = caches[cache_name]
    cache_key = _make_cache_key(group, window, rate, value, method)

    count = None
    added = cache.add(cache_key, initial_value, period + EXPIRATION_FUDGE)
    if added:
        count = initial_value
    else:
        if increment:
            try:
                # python3-memcached will throw a ValueError if the server is
                # unavailable or (somehow) the key doesn't exist. redis, on the
                # other hand, simply returns None.
                count = cache.incr(cache_key)
            except ValueError:
                pass
        else:
            count = cache.get(cache_key, initial_value)

    # Getting or setting the count from the cache failed
    if count is None:
        if getattr(settings, 'RATELIMIT_FAIL_OPEN', False):
            return None
        return {
            'count': 0,
            'limit': 0,
            'should_limit': True,
            'time_left': -1,
        }

    time_left = window - int(time.time())
    return {
        'count': count,
        'limit': limit,
        'should_limit': count > limit,
        'time_left': time_left,
    }


is_ratelimited.ALL = ALL
is_ratelimited.UNSAFE = UNSAFE
get_usage.ALL = ALL
get_usage.UNSAFE = UNSAFE
