from django.core.exceptions import PermissionDenied


try:
    from rest_framework.exceptions import Throttled
except ImportError:
    class Ratelimited(PermissionDenied):
        pass
else:
    class Ratelimited(PermissionDenied, Throttled):
        pass
