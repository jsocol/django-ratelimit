from datetime import timedelta

from django.test import TestCase, override_settings
from django_ratelimit.record_handlers.helpers import resolve_cache_timeout


def mock_resolve_cache_timeout_str():
    return timedelta(seconds=30)


class RateLimitCacheRecordTimeTestCase(TestCase):
    @override_settings(RATELIMIT_CACHE_RECORD_TIME=None)
    def test_resolve_cache_timeout_none(self):
        self.assertIsNone(resolve_cache_timeout())

    @override_settings(RATELIMIT_CACHE_RECORD_TIME=2)
    def test_resolve_cache_timeout_int(self):
        self.assertEqual(resolve_cache_timeout(), timedelta(hours=2))

    @override_settings(RATELIMIT_CACHE_RECORD_TIME=lambda: timedelta(seconds=30))
    def test_resolve_cache_timeout_callable(self):
        self.assertEqual(resolve_cache_timeout(), timedelta(seconds=30))

    @override_settings(
        RATELIMIT_CACHE_RECORD_TIME="django_ratelimit.tests.test_record_handlers.test_helpers.mock_resolve_cache_timeout_str"
    )
    def test_resolve_cache_timeout_path(self):
        self.assertEqual(resolve_cache_timeout(), timedelta(seconds=30))
