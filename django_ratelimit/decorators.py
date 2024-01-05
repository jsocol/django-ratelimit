from functools import wraps
import django
if django.VERSION >= (4, 1):
    from asgiref.sync import iscoroutinefunction
else:
    def iscoroutinefunction(func):
        return False

from django.conf import settings
from django.utils.module_loading import import_string

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.exceptions import Ratelimited
from django_ratelimit.core import is_ratelimited


__all__ = ['ratelimit']


def ratelimit(group=None, key=None, rate=None, method=ALL, block=True):
    def decorator(fn):
        # if iscoroutinefunction(fn):
        #     @wraps(fn)
        #     async def _async_wrapped(request, *args, **kw):
        #         old_limited = getattr(request, 'limited', False)
        #         ratelimited = is_ratelimited(
        #             request=request, group=group, fn=fn, key=key, rate=rate,
        #             method=method, increment=True)
        #         request.limited = ratelimited or old_limited
        #         if ratelimited and block:
        #             cls = getattr(
        #                 settings, 'RATELIMIT_EXCEPTION_CLASS', Ratelimited)
        #             if isinstance(cls, str):
        #                 cls = import_string(cls)
        #             raise cls()
        #         return await fn(request, *args, **kw)
        #     return _async_wrapped

        @wraps(fn)
        def _wrapped(request, *args, **kw):
            old_limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(request=request, group=group, fn=fn,
                                         key=key, rate=rate, method=method,
                                         increment=True)
            request.limited = ratelimited or old_limited
            if ratelimited and block:
                cls = getattr(
                    settings, 'RATELIMIT_EXCEPTION_CLASS', Ratelimited)
                if isinstance(cls, str):
                    cls = import_string(cls)
                raise cls()
            return fn(request, *args, **kw)
        return _wrapped
    return decorator


ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
