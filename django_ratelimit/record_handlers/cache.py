from logging import getLogger

from django_ratelimit.record_handlers.base import AbstractRateLimitRecordHandler
from django_ratelimit.record_handlers.helpers import (
    get_cache,
    get_cache_timeout,
    get_client_cache_key,
    get_client_ip_address,
    get_client_user_agent,
    get_client_username,
)

log = getLogger(__name__)


class CacheRecordHandler(AbstractRateLimitRecordHandler):
    """
    Handler implementation for limit exceeded records in cache
    """

    def __init__(self) -> None:
        self.cache = get_cache()
        self.cache_timeout = get_cache_timeout()

    def exceeded_limit_record(self, request):
        """
        When rate limit for api is exceeded, save attempt record in cache,
        and if it already exists update access attempt failures.
        """

        if request is None:
            log.error(
                "DRL: CacheRecordHandler.exceeded_limit_record does not function without a request."
            )
            return

        username = get_client_username(request)
        ip_address = get_client_ip_address(request)
        user_agent = get_client_user_agent(request)

        cache_key = get_client_cache_key(username, ip_address, user_agent)
        attempts = self.cache.get(cache_key, default=dict()).get("attempts", 0)
        self.cache.set(
            cache_key,
            {"attempts": attempts + 1, "ip_address": ip_address},
            self.cache_timeout,
        )
