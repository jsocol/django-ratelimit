from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from ratelimit.models import ExceededLimitRecord
from ratelimit.record_handlers.database import DatabaseRecordHandler
from ratelimit.record_handlers.proxy import RateLimitRecordProxy


class RateLimitRecordProxyHandlerTestCase(TestCase):
    @patch("ratelimit.record_handlers.proxy.RateLimitRecordProxy.implementation", None)
    def test_setting_changed_signal_triggers_handler_reimport(self):
        self.assertIsNone(RateLimitRecordProxy.implementation)

        with self.settings(
            RATELIMIT_RECORD_HANDLER="ratelimit.record_handlers.database.DatabaseRecordHandler"
        ):
            self.assertIsNotNone(RateLimitRecordProxy.implementation)


class DatabaseRecordHandlerTestCase(TestCase):
    def setUp(self):
        self.username = "username"
        self.password = "secure password"
        self.email = "justanemail@bettertommorow.ocm"
        self.ip_address = "127.0.0.1"
        self.user_agent = "agent connor from Detroit Become Human"
        self.path_info = reverse("admin:login")
        self.user = get_user_model().objects.create_superuser(
            username=self.username, password=self.password, email=self.email
        )
        self.request = HttpRequest()
        self.request.method = "POST"
        self.request.META["REMOTE_ADDR"] = self.ip_address
        self.request.META["HTTP_USER_AGENT"] = self.user_agent
        self.request.META["PATH_INFO"] = self.path_info
        self.request.user = self.user

    def test_database_record(self):
        DatabaseRecordHandler.exceeded_limit_record(self, request=self.request)
        model_object = ExceededLimitRecord.objects.first()
        self.assertEquals(self.user_agent, model_object.user_agent)
        self.assertEquals(self.ip_address, model_object.ip_address)
        self.assertEquals(self.path_info, model_object.path_info)
        self.assertEquals(1, ExceededLimitRecord.objects.count())
