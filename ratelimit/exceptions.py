from django.core.exceptions import PermissionDenied


class Ratelimited(PermissionDenied):
    pass
