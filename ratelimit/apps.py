from __future__ import unicode_literals

from django.apps import AppConfig


class RateLimitConfig(AppConfig):
    name = "ratelimit"

    def ready(self):
        import ratelimit.signals
