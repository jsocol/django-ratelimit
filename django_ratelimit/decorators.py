from functools import wraps

from django.conf import settings
from django.utils.module_loading import import_string

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.exceptions import Ratelimited
from django_ratelimit.core import get_usage


__all__ = ['ratelimit']


def ratelimit(group=None, key=None, rate=None, method=ALL, block=True):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kw):
            old_limited = getattr(request, 'limited', False)

            usage = get_usage(request=request, group=group, fn=fn,
                              key=key, rate=rate, method=method,
                              increment=True)
            if usage is None:
                ratelimited = False
            else:
                ratelimited = usage['should_limit']

            request.limited = ratelimited or old_limited
            request.usage = usage

            if ratelimited and block:
                cls = getattr(
                    settings, 'RATELIMIT_EXCEPTION_CLASS', Ratelimited)
                exc = (import_string(cls) if isinstance(cls, str) else cls)()
                exc.usage = usage
                raise exc
            return fn(request, *args, **kw)
        return _wrapped
    return decorator


ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
