from django.core.signals import setting_changed
from django.dispatch import receiver

from ratelimit.record_handlers.proxy import RateLimitRecordProxy


@receiver(setting_changed)
def handle_setting_changed(sender, setting, value, enter, **kwargs):
    """
    Reinitialize handler implementation if a relevant setting changes
    in e.g. application reconfiguration or during testing.
    """

    if setting == "RATELIMIT_RECORD_HANDLER":
        RateLimitRecordProxy.get_implementation(force=True)
