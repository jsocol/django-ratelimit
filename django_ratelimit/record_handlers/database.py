from logging import getLogger

from django.db.models import F
from django_ratelimit.models import ExceededLimitRecord
from django_ratelimit.record_handlers.base import AbstractRateLimitRecordHandler
from django_ratelimit.record_handlers.helpers import (
    get_client_ip_address,
    get_client_path_info,
    get_client_user_agent,
    get_client_username,
)

log = getLogger(__name__)


class DatabaseRecordHandler(AbstractRateLimitRecordHandler):
    """
    Handler implementation for limit exceeded records in database.
    """

    def exceeded_limit_record(self, request) -> None:
        """
        When rate limit for api is exceeded, save attempt record in database,
        and if it already exists update access attempt failures.
        """
        if request is None:
            log.error(
                "DRL: DatabaseRecordHandler.exceeded_limit_record does not function without a request."
            )
            return
        client_ip_address = get_client_ip_address(request)
        username = get_client_username(request)
        path_info = get_client_path_info(request)
        user_agent = get_client_user_agent(request)

        try:
            limit_record = ExceededLimitRecord.objects.only("id").get(
                user_agent=user_agent,
                ip_address=client_ip_address,
                username=username,
                path_info=path_info,
            )
            limit_record.access_attempt_failures = F("access_attempt_failures") + 1
            limit_record.save()

        except ExceededLimitRecord.DoesNotExist:
            ExceededLimitRecord.objects.create(
                user_agent=user_agent,
                ip_address=client_ip_address,
                username=username,
                path_info=path_info,
                access_attempt_failures=1,
            )
