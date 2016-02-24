from __future__ import absolute_import

from functools import wraps

from django.http import HttpRequest

from ratelimit import ALL, UNSAFE
from ratelimit.exceptions import Ratelimited
from ratelimit.utils import is_ratelimited


__all__ = ['ratelimit']


def ratelimit(group=None, key=None, rate=None, method=ALL, block=False,
              args_to_request=True):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(*args, **kw):
            # Work as a CBV method decorator.
            if isinstance(args[0], HttpRequest):
                request = args[0]
            else:
                request = args[1]
            if args_to_request:
                request.ratelimit_args = {'group': group, 'key': key,
                                          'rate': rate, 'method': method,
                                          'block': block, 'fn': fn}
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
