from functools import wraps

from ratelimit.exceptions import Ratelimited
from ratelimit.helpers import is_ratelimited


__all__ = ['ratelimit']


def ratelimit(ip=True, block=False, method=['POST'], field=None, rate='5/m',
              skip_if=None, keys=None):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kw):
            request.limited = getattr(request, 'limited', False)
            if skip_if is None or not skip_if(request):
                ratelimited = is_ratelimited(request=request, increment=True,
                                             ip=ip, method=method, field=field,
                                             rate=rate, keys=keys)
                if ratelimited and block:
                    raise Ratelimited()
            return fn(request, *args, **kw)
        return _wrapped
    return decorator
