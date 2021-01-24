from django.conf import settings
from django.utils.module_loading import import_string

from ratelimit.exceptions import Ratelimited


class RatelimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Sets REMOTE_ADDR correctly to the client's ip, if REMOTE_ADDR is missing.
        It happens when django is run with a domain socket server (eg. gunicorn).
        ref: https://stackoverflow.com/a/34254843/1031191
        """
        if not request.META("REMOTE_ADDR", "") and "HTTP_X_FORWARDED_FOR" in request.META:
            parts = request.META["HTTP_X_FORWARDED_FOR"].split(",", 1)
            request.META["REMOTE_ADDR"] = parts[0]

        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, Ratelimited):
            return None
        view = import_string(settings.RATELIMIT_VIEW)
        return view(request, exception)
