from __future__ import unicode_literals

from django.apps import AppConfig


class RateLimitConfig(AppConfig):
    name = "django_ratelimit"

    def ready(self):
        import django_ratelimit.signals
