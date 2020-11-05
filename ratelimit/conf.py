from django.conf import settings

# if True, records exceeded limits and attempts
settings.RATELIMIT_RECORD = getattr(settings, "RATELIMIT_RECORD", False)

# timeout time to store records in cache
# six days by default
SIX_DAYS = 6 * 24
settings.RATELIMIT_CACHE_RECORD_TIME = getattr(
    settings, "RATELIMIT_CACHE_RECORD_TIME", SIX_DAYS
)

# register an admin panel for records
settings.RATELIMIT_ENABLE_ADMIN = getattr(settings, "RATELIMIT_ENABLE_ADMIN", True)

# cache or database record handler
# database by default
settings.RATELIMIT_RECORD_HANDLER = getattr(
    settings,
    "RATELIMIT_RECORD_HANDLER",
    "ratelimit.record_handlers.database.DatabaseRecordHandler",
)
