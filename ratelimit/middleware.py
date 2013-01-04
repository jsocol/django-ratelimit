from django.conf import settings
from django.utils.importlib import import_module

from ratelimit.exceptions import Ratelimited


class RatelimitMiddleware(object):
    def process_exception(self, request, exception):
        if not isinstance(exception, Ratelimited):
            return
        module_name, _, view_name = settings.RATELIMIT_VIEW.rpartition('.')
        module = import_module(module_name)
        view = getattr(module, view_name)
        return view(request, exception)
