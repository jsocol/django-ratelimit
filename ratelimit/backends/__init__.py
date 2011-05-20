class BaseBackend(object):
    """Backends should implement this interface."""
    def count(self, request, ip=True, field=None, period=60):
        raise NotImplementedError

    def limit(self, request, ip=True, field=None, count=5):
        raise NotImplementedError
