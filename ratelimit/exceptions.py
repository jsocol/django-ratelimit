from django.core.exceptions import PermissionDenied


class Ratelimited(PermissionDenied):
    pass


class InvalidConfig(Exception):
    pass
