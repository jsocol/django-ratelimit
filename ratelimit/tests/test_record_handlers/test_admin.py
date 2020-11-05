from contextlib import suppress
from importlib import reload

from django.contrib import admin
from django.test import TestCase, override_settings

import ratelimit.admin
from ratelimit.models import ExceededLimitRecord


class RateLimitAdminFlag(TestCase):
    def setUp(self):
        with suppress(admin.sites.NotRegistered):
            admin.site.unregister(ExceededLimitRecord)

    @override_settings(RATELIMIT_ENABLE_ADMIN=False)
    def test_disable_admin(self):
        reload(ratelimit.admin)
        self.assertFalse(admin.site.is_registered(ExceededLimitRecord))

    def test_enable_admin_by_default(self):
        reload(ratelimit.admin)
        self.assertTrue(admin.site.is_registered(ExceededLimitRecord))
