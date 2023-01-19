import ipaddress
import functools
import hashlib
import re
import socket
import time
import zlib

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from django_ratelimit import ALL, UNSAFE


__all__ = ['is_ratelimited', 'get_usage']

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

# Extend the expiration time by a few seconds to avoid misses.
EXPIRATION_FUDGE = 5


def _get_ip(request):
    ip_meta = getattr(settings, 'RATELIMIT_IP_META_KEY', None)
    if not ip_meta:
        ip = request.META['REMOTE_ADDR']
        if not ip:
            raise ImproperlyConfigured(
                'IP address in REMOTE_ADDR is empty. This can happen when '
                'using a reverse proxy and connecting to the app server with '
                'Unix sockets. See the documentation for '
                'RATELIMIT_IP_META_KEY: https://bit.ly/3iIpy2x')
    elif callable(ip_meta):
        ip = ip_meta(request)
    elif isinstance(ip_meta, str) and '.' in ip_meta:
        ip_meta_fn = import_string(ip_meta)
        ip = ip_meta_fn(request)
    elif ip_meta in request.META:
        ip = request.META[ip_meta]
    else:
        raise ImproperlyConfigured(
            'Could not get IP address from "%s"' % ip_meta)

    if ':' in ip:
        # IPv6
        mask = getattr(settings, 'RATELIMIT_IPV6_MASK', 64)
    else:
        # IPv4
        mask = getattr(settings, 'RATELIMIT_IPV4_MASK', 32)

    network = ipaddress.ip_network(f'{ip}/{mask}', strict=False)

    return str(network.network_address)


def user_or_ip(request):
    if request.user.is_authenticated:
        return str(request.user.pk)
    return _get_ip(request)


_SIMPLE_KEYS = {
    'ip': lambda r: _get_ip(r),
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
    """
    Given a value, and time period return when the end of the current time
    period for rate evaluation is.
    """
    ts = int(time.time())
    if period == 1:
        return ts
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    # This logic determines either the last or current end of a time period.
    # Subtracting (ts % period) gives us the a consistent edge from the epoch.
    # We use (zlib.crc32(value) % period) to add a consistent jitter so that
    # all time periods don't end at the same time.
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(group, window, rate, value, methods):
    count, period = _split_rate(rate)
    safe_rate = '%d/%ds' % (count, period)
    parts = [group, safe_rate, value, str(window)]
    if methods is not None:
        if methods == ALL:
            methods = ''
        elif isinstance(methods, (list, tuple)):
            methods = ''.join(sorted([m.upper() for m in methods]))
        parts.append(methods)
    prefix = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')
    attr = getattr(settings, 'RATELIMIT_HASH_ALGORITHM', hashlib.sha256)
    algo_cls = (import_string(f'{attr}')
                if isinstance(attr, str)
                else attr
                )
    return prefix + algo_cls(''.join(parts).encode('utf-8')).hexdigest()


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
    elif isinstance(rate, str) and '.' in rate:
        ratefn = import_string(rate)
        rate = ratefn(group, request)

    if rate is None:
        return None
    limit, period = _split_rate(rate)
    if period <= 0:
        raise ImproperlyConfigured('Ratelimit period must be greater than 0')

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
    try:
        added = cache.add(cache_key, initial_value, period + EXPIRATION_FUDGE)
    except socket.gaierror:  # for redis
        added = False
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
    if count is None or count is False:
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
