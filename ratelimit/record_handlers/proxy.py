from django.utils.module_loading import import_string
from ratelimit.conf import settings
from ratelimit.record_handlers.base import (
    AbstractRateLimitRecordHandler,
    RateLimitRecordHandler,
)
from ratelimit.record_handlers.helpers import toggleable


class RateLimitRecordProxy(AbstractRateLimitRecordHandler):
    """
    Proxy interface for configurable Django-RateLimit records handler class.
    """

    implementation = None

    @classmethod
    def get_implementation(cls, force: bool = False) -> RateLimitRecordHandler:
        """
        Singleton Pattern to avoid re-initialization.

        This method is re-entrant and can be called multiple times from e.g. Django application loader.
        """

        if force or not cls.implementation:
            cls.implementation = import_string(settings.RATELIMIT_RECORD_HANDLER)()
        return cls.implementation

    @classmethod
    @toggleable
    def exceeded_limit_record(cls, request, **kwargs):
        return cls.get_implementation().exceeded_limit_record(request, **kwargs)
