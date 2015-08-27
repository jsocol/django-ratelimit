
from ratelimit.exceptions import Ratelimited
import rest_framework.views
import rest_framework.exceptions

def exception_handler(exc, context):
    if isinstance(exc, Ratelimited):
        exc = rest_framework.exceptions.Throttled()

    return rest_framework.views.exception_handler(exc, context)
