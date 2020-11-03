from django.contrib import admin

from ratelimit.conf import settings
from ratelimit.models import ExceededLimitRecord


class ExceededLimitRecordAdmin(admin.ModelAdmin):
    list_display = (
        "blocked_at",
        "last_blocked_at",
        "ip_address",
        "user_agent",
        "username",
        "path_info",
        "access_attempt_failures",
    )

    list_filter = ["blocked_at", "path_info", "last_blocked_at"]

    search_fields = ["ip_address", "username", "user_agent", "path_info"]

    date_hierarchy = "last_blocked_at"

    readonly_fields = [
        "user_agent",
        "ip_address",
        "username",
        "path_info",
        "blocked_at",
        "access_attempt_failures",
        "last_blocked_at",
    ]

    def has_add_permission(self, request):
        return False


if settings.RATELIMIT_ENABLE_ADMIN:
    admin.site.register(ExceededLimitRecord, ExceededLimitRecordAdmin)
