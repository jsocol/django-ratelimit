from functools import wraps

from django.http import HttpResponseForbidden

from ratelimit.backends.cachebe import CacheBackend


def _method_match(request, method=None):
    if method is None:
        method = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
    if not isinstance(method, list):
        method = [method]
    return request.method in method


_backend = CacheBackend()


def ratelimit(ip=True, block=False, method=None, field=None, rate=5):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kw):
            if _method_match(request, method):
                if _backend.limit(request, ip, field, rate):
                    if block:
                        return HttpResponseForbidden()
                    request.limited = True
                _backend.count(request, ip, field)
            return fn(request, *args, **kw)
        return _wrapped
    return decorator
