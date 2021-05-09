from django.core.exceptions import PermissionDenied


try:
    from rest_framework.exceptions import Throttled

    class Ratelimited(PermissionDenied):
        pass
except ImportError:
    class Ratelimited(PermissionDenied, Throttled):
        pass
