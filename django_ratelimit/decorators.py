from functools import wraps

from django.conf import settings
from django.utils.module_loading import import_string

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.exceptions import Ratelimited
from django_ratelimit.core import is_ratelimited, ais_ratelimited
from asgiref.sync import iscoroutinefunction


__all__ = ['ratelimit']


def ratelimit(group=None, key=None, rate=None, method=ALL, block=True):
    def decorator(fn):
        if iscoroutinefunction(fn):
            @wraps(fn)
            async def _wrapped(request, *args, **kw):
                old_limited = getattr(request, 'limited', False)
                ratelimited = await ais_ratelimited(request=request, group=group, fn=fn,
                                            key=key, rate=rate, method=method,
                                            increment=True)
                request.limited = ratelimited or old_limited
                if ratelimited and block:
                    cls = getattr(
                        settings, 'RATELIMIT_EXCEPTION_CLASS', Ratelimited)
                    raise (import_string(cls) if isinstance(cls, str) else cls)()
                return await fn(request, *args, **kw)
        else:
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
                    raise (import_string(cls) if isinstance(cls, str) else cls)()
                return fn(request, *args, **kw)
        return _wrapped

    return decorator

ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
