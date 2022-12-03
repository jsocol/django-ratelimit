from django.apps import AppConfig


class DjangoRatelimitConfig(AppConfig):
    name = 'django_ratelimit'
    label = 'ratelimit'
    default = True

    def ready(self):
        from . import checks  # noqa: F401
