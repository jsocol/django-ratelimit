from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    user_agent = models.CharField(_("User Agent"), max_length=255)
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, db_index=True)
    username = models.CharField(_("Username"), max_length=255, null=True, db_index=True)
    path_info = models.CharField(_("Path"), max_length=255)
    blocked_at = models.DateTimeField(_("Blocked At"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "ratelimit"
        ordering = ["-blocked_at"]


class ExceededLimitRecord(BaseModel):
    access_attempt_failures = models.PositiveIntegerField(
        _("Access Attempt Failure Count")
    )
    last_blocked_at = models.DateTimeField(_("Last Blocked At"), auto_now=True)

    def __str__(self):
        return "{}".format(self.access_attempt_failures)

    class Meta:
        verbose_name = _("exceeded limit record")
        verbose_name_plural = _("exceeded limit records")
