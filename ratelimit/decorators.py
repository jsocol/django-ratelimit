from __future__ import absolute_import

from functools import wraps

from ratelimit import ALL, UNSAFE
from ratelimit.exceptions import Ratelimited
from ratelimit.utils import is_ratelimited

__all__ = ['ratelimit']

def _looks_like_HttpRequest(thing):
    # Django Rest Framework uses a Request class that is not a subclass of
    # Django core's HttpRequest, so we duck-type the request object
    try:
        thing.META.get('REQUEST_METHOD')
        thing.method
        thing.path
        thing.scheme
        return True
    except AttributeError:
        return False

def ratelimit(group=None, key=None, rate=None, method=ALL, block=False):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(*args, **kw):
            # Work as a function-based view decorator or CBV method decorator.
            if _looks_like_HttpRequest(args[0]):
                request = args[0]
            elif len(args) >= 2 and _looks_like_HttpRequest(args[1]):
                request = args[1]
            else:
                raise ValueError('ratelimit decorator wrapped around something that does not look like a view')
            request.limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(request=request, group=group, fn=fn,
                                         key=key, rate=rate, method=method,
                                         increment=True)
            if ratelimited and block:
                raise Ratelimited()
            return fn(*args, **kw)
        return _wrapped
    return decorator


ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
