from functools import wraps

from ratelimit.exceptions import Ratelimited
from ratelimit.utils import is_ratelimited


__all__ = ['ratelimit']


def ratelimit(group=None, key=None, rate=None, method='POST', block=False):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kw):
            request.limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(request=request, group=group, key=key,
                                         rate=rate, method=method)
            if ratelimited and block:
                raise Ratelimited()
            return fn(request, *args, **kw)
        return _wrapped
    return decorator
