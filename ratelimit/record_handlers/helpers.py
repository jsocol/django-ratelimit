from datetime import timedelta
from hashlib import md5
from typing import Callable, Optional

import ipware.ip
from django.core.cache import BaseCache, caches
from django.http import HttpRequest
from django.utils.module_loading import import_string

from ratelimit.conf import settings


def get_client_ip_address(request) -> str:
    """
    Get client IP address from request.

    The django-ipware package is used for address resolution.
    """

    client_ip_address, _ = ipware.ip.get_client_ip(request)
    return client_ip_address


def get_client_user_agent(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "<unknown>")[:255]


def get_client_path_info(request) -> str:
    return request.META.get("PATH_INFO", "<unknown>")[:255]


def get_client_username(request) -> str:
    if request.user.is_authenticated:
        return request.user.username
    return "Anonymous"


def toggleable(func) -> Callable:
    """
    Decorator that toggles function execution based on settings.

    If the ``settings.RATELIMIT_RECORD`` flag is set to ``False``
    the decorated function never runs and a None is returned.

    This decorator is only suitable for functions that do not
    require return values to be passed back to callers.
    """

    def inner(*args, **kwargs):
        if settings.RATELIMIT_RECORD:
            return func(*args, **kwargs)

    return inner


def get_cache() -> BaseCache:
    """
    Get the cache instance RateLimit is configured to use with ``settings.RATELIMIT_USE_CACHE``
    and use ``'default'`` if not set.
    """

    return caches[getattr(settings, "RATELIMIT_USE_CACHE", "default")]


def get_cache_timeout() -> Optional[int]:
    """
    Return the cache timeout interpreted from settings.RATELIMIT_CACHE_RECORD_TIME.

    The cache timeout can be either None if not configured or integer of seconds if configured.

    Notice that the settings.RATELIMIT_CACHE_RECORDS_TIME can be None, timedelta, integer, callable, or str path,
    and this function offers a unified _integer or None_ representation of that configuration
    for use with the Django cache backends.
    """

    cache_timeout = resolve_cache_timeout()
    if cache_timeout is None:
        return None
    return int(cache_timeout.total_seconds())


def resolve_cache_timeout() -> Optional[timedelta]:
    """
    For use within get_cache_timeout function.

    The return value is either None or timedelta.

    :exception TypeError: if settings.RATELIMIT_CACHE_RECORD_TIME is of wrong type.
    """

    cache_timeout = settings.RATELIMIT_CACHE_RECORD_TIME

    if isinstance(cache_timeout, int):
        return timedelta(hours=cache_timeout)
    if isinstance(cache_timeout, str):
        return import_string(cache_timeout)()
    if callable(cache_timeout):
        return cache_timeout()

    return cache_timeout


def make_cache_key(key_components):

    cache_key_components = "".join(value for value in key_components.values() if value)
    cache_key_digest = md5(cache_key_components.encode()).hexdigest()
    cache_key = f"drl-{cache_key_digest}"

    return cache_key


def get_client_cache_key(request: HttpRequest) -> str:
    """
    Build cache key name from request.

    :return cache_key: Hash key that is usable for Django cache backends
    """

    username = get_client_username(request)
    ip_address = get_client_ip_address(request)
    user_agent = get_client_user_agent(request)

    key_components = {
        "username": username,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    return make_cache_key(key_components)
