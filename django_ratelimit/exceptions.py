import json

from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder


class Ratelimited(PermissionDenied):

    def __init__(self, *args, usage=None, **kwargs):
        self.usage = usage
        super().__init__(*args, **kwargs)
        # If python >=3.11 (has add_note), then add jsonified self.usage as note
        if hasattr(self, "add_note"):
            self.add_note("Usage: " + json.dumps(
                self.usage,
                indent=2,
                cls=DjangoJSONEncoder,
                default=lambda obj: str(obj),
            ))
