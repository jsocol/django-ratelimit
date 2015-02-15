from __future__ import absolute_import

from ratelimit import ALL, UNSAFE
from ratelimit.decorators import ratelimit


__all__ = ['RatelimitMixin']


class RatelimitMixin(object):
    """
    Mixin for usage in Class Based Views
    configured with the decorator ``ratelimit`` defaults.

    Configure the class-attributes prefixed with ``ratelimit_``
    for customization of the ratelimit process.

    Example::

        class ContactView(RatelimitMixin, FormView):
            form_class = ContactForm
            template_name = "contact.html"

            # Limit contact form by remote address.
            ratelimit_key = 'ip'
            ratelimit_block = True

            def form_valid(self, form):
                # Whatever validation.
                return super(ContactView, self).form_valid(form)

    """
    ratelimit_group = None
    ratelimit_key = None
    ratelimit_rate = '5/m'
    ratelimit_block = False
    ratelimit_method = ALL

    ALL = ALL
    UNSAFE = UNSAFE

    def get_ratelimit_config(self):
        return dict(
            (attr[len("ratelimit_"):], getattr(self.__class__, attr))
            for attr in dir(self.__class__)
            if attr.startswith("ratelimit")
        )

    def dispatch(self, *args, **kwargs):
        return ratelimit(
            **self.get_ratelimit_config()
        )(super(RatelimitMixin, self).dispatch)(*args, **kwargs)
