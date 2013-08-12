# -*- coding: utf-8 -*-

from .decorators import ratelimit


class RateLimitMixin(object):
    """
    Mixin for usage in Class Based Views
    configured with the decorator ``ratelimit`` defaults.

    Configure the class-attributes prefixed with ``ratelimit_``
    for customization of the ratelimit process.

    Example::

        class ContactView(RateLimitMixin, FormView):
            form_class = ContactForm
            template_name = "contact.html"

            ratelimit_block = True

            def form_valid(self, form):
                # do sth. here
                return super(ContactView, self).form_valid(form)

    """
    ratelimit_ip = True
    ratelimit_block = False
    ratelimit_method = ['POST']
    ratelimit_field = None
    ratelimit_rate = '5/m'
    ratelimit_skip_if = None
    ratelimit_keys = None

    def get_ratelimit_config(self):
        return dict(
            (k[len("ratelimit_"):], v)
            for k, v in vars(self.__class__).items()
            if k.startswith("ratelimit")
        )

    def dispatch(self, *args, **kwargs):
        return ratelimit(
            **self.get_ratelimit_config()
        )(super(RateLimitMixin, self).dispatch)(*args, **kwargs)
