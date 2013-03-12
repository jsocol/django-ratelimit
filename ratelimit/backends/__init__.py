class BaseBackend(object):
    """Backends should implement this interface."""
    def count(self, request, key_func, period):
        raise NotImplementedError

    def limit(self, request, key_func, count):
        raise NotImplementedError

    def key_transform(self, request, key_funcs):
        keys = []
        if not isinstance(key_funcs, (list, tuple)):
            key_funcs = [key_funcs]
        for k in key_funcs:
            if callable(k):
                keys.extend(k(request))
            else:
                keys.append(k)
        return keys
