from unittest.mock import MagicMock, patch

from django.test import TestCase

from ratelimit.record_handlers.proxy import RateLimitRecordProxy


class RateLimitRecordProxyHandlerTestCase(TestCase):
    def setUp(self):
        self.request = MagicMock()
        self.user = MagicMock()

    @patch("ratelimit.record_handlers.proxy.RateLimitRecordProxy.implementation", None)
    def test_setting_changed_signal_triggers_handler_reimport(self):
        self.assertIsNone(RateLimitRecordProxy.implementation)
        print(RateLimitRecordProxy.implementation)

        with self.settings(
            RATELIMIT_RECORD_HANDLER="ratelimit.record_handlers.cache.CacheRecordHandler"
        ):
            print(RateLimitRecordProxy.implementation)
            self.assertIsNotNone(RateLimitRecordProxy.implementation)
