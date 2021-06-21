from abc import ABC, abstractmethod


class AbstractRateLimitRecordHandler(ABC):
    @abstractmethod
    def exceeded_limit_record(self, request) -> None:
        """
        Checks and creates a record of exceeded limits if needed.

        This is a virtual method that needs an implementation in the handler subclass
        if the ``settings.RATELIMIT_RECORD`` flag is set to ``True``.
        """
        raise NotImplementedError("exceeded_limit_record should be implemented")


class RateLimitRecordHandler(AbstractRateLimitRecordHandler):
    def exceeded_limit_record(self, request) -> None:
        """
        Default bare handler
        """
