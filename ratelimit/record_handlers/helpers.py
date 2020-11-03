from typing import Callable

import ipware.ip
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
