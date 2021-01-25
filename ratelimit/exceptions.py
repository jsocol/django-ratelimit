from django.core.exceptions import PermissionDenied


class Ratelimited(PermissionDenied):

    def __init__(self, group, key, rate):
        super(Ratelimited, self).__init__()
        self.group = group
        self.key = key
        self.rate = rate
