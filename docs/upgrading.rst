.. _upgrading-chapter:

=============
Upgrade Notes
=============

See also the CHANGELOG_.

.. _CHANGELOG: https://github.com/jsocol/django-ratelimit/blob/main/CHANGELOG

.. _upgrading-3.0:

From 2.0 to 3.0
===============

Quickly:

- Ratelimit now supports Django >=1.11 and Python >=3.4.
- ``@ratelimit`` no longer works directly on class methods, add
  ``@method_decorator``.
- ``RatelimitMixin`` is gone, migrate to ``@method_decorator``.
- Moved ``is_ratelimted`` method from ``ratelimit.utils`` to
  ``ratelimit.core``.

``@ratelimit`` decorator on class methods
-----------------------------------------

In 3.0, the decorator has been simplified and must now be used with
Django's excellent ``@method_decorator`` utility. Migrating should be
relatively straight-forward:

.. code-block:: python

    from django.views.generic import View
    from ratelimit.decorators import ratelimit

    class MyView(View):
        @ratelimit(key='ip', rate='1/m', method='GET')
        def get(self, request):
            pass

changes to

.. code-block:: python

    from django.utils.decorators import method_decorator
    from django.views.generic import View
    from ratelimit.decorators import ratelimit

    class MyView(View):
        @method_decorator(ratelimit(key='ip', rate='1/m', method='GET'))
        def get(self, request):
            pass

``RatelimitMixin``
------------------

``RatelimitMixin`` is a vestige of an older version of Ratelimit that
did not support multiple rates per method. As such, it is significantly
less powerful than the current ``@ratelimit`` decorator. To migrate to
the decorator, use the ``@method_decorator`` from Django:

.. code-block:: python

    class MyView(RatelimitMixin, View):
        ratelimit_key = 'ip'
        ratelimit_rate = '10/m'
        ratelimit_method = 'GET'

        def get(self, request):
            pass

becomes

.. code-block:: python

    class MyView(View):
        @method_decorator(ratelimit(key='ip', rate='10/m', method='GET'))
        def get(self, request):
            pass

The major benefit is that it is now possible to apply multiple limits to
the same method, as with :ref:`the decorator <usage-decorator>`_.



.. _upgrading-0.5:

From <=0.4 to 0.5
=================

Quickly:

- Rate limits are now counted against fixed, instead of sliding,
  windows.
- Rate limits are no longer shared between methods by default.
- Change ``ip=True`` to ``key='ip'``.
- Drop ``ip=False``.
- A key must always be specified. If using without an explicit key, add
  ``key='ip'``.
- Change ``fields='foo'`` to ``post:foo`` or ``get:foo``.
- Change ``keys=callable`` to ``key=callable``.
- Change ``skip_if`` to a callable ``rate=<callable>`` method (see
  :ref:`Rates <rates-chapter>`.
- Change ``RateLimitMixin`` to ``RatelimitMixin`` (note the lowercase
  ``l``).
- Change ``ratelimit_ip=True`` to ``ratelimit_key='ip'``.
- Change ``ratelimit_fields='foo'`` to ``post:foo`` or ``get:foo``.
- Change ``ratelimit_keys=callable`` to ``ratelimit_key=callable``.


Fixed windows
-------------

Before 0.5, rates were counted against a *sliding* window, so if the
rate limit was ``1/m``, and three requests came in::

    1.2.3.4 [09/Sep/2014:12:25:03] ...
    1.2.3.4 [09/Sep/2014:12:25:53] ... <RATE LIMITED>
    1.2.3.4 [09/Sep/2014:12:25:59] ... <RATE LIMITED>

Even though the third request came nearly two minutes after the first
request, the second request moved the window. Good actors could easily
get caught in this, even trying to implement reasonable back-offs.

Starting in 0.5, windows are *fixed*, and staggered throughout a given
period based on the key value, so the third request, above would not be
rate limited (it's possible neither would the second one).

.. warning::
   That means that given a rate of ``X/u``, you may see up to ``2 * X``
   requests in a short period of time. Make sure to set ``X``
   accordingly if this is an issue.

This change still limits bad actors while being far kinder to good
actors.


Staggering windows
^^^^^^^^^^^^^^^^^^

To avoid a situation where all limits expire at the top of the hour,
windows are automatically staggered throughout their period based on the
key value. So if, for example, two IP addresses are hitting hourly
limits, instead of both of those limits expiring at 06:00:00, one might
expire at 06:13:41 (and subsequently at 07:13:41, etc) and the other
might expire at 06:48:13 (and 07:48:13, etc).


Sharing rate limits
-------------------

Before 0.5, rate limits were shared between methods based only on their
keys. This was very confusing and unintuitive, and is far from the
least-surprising_ thing. For example, given these three views::

    @ratelimit(ip=True, field='username')
    def both(request):
        pass

    @ratelimit(ip=False, field='username')
    def field_only(request):
        pass

    @ratelimit(ip=True)
    def ip_only(request):
        pass


The pair ``both`` and ``field_only`` shares one rate limit key based on
all requests to either (and any other views) containing the same
``username`` key (in ``GET`` or ``POST``), regardless of IP address.

The pair ``both`` and ``ip_only`` shares one rate limit key based on the
client IP address, along with all other views.

Thus, it's extremely difficult to determine exactly why a request is
getting rate limited.

In 0.5, methods never share rate limits by default. Instead, limits are
based on a combination of the :ref:`group <usage-decorator>`, rate, key
value, and HTTP methods *to which the decorator applies* (i.e. **not**
the method of the request). This better supports common use cases and
stacking decorators, and still allows decorators to be shared.

For example, this implements an hourly rate limit with a per-minute
burst rate limit::

    @ratelimit(key='ip', rate='100/m')
    @ratelimit(key='ip', rate='1000/h')
    def myview(request):
        pass

However, this view is limited *separately* from another view with the
same keys and rates::

    @ratelimit(key='ip', rate='100/m')
    @ratelimit(key='ip', rate='1000/h')
    def anotherview(request):
        pass

To cause the views to share a limit, explicitly set the ``group``
argument::

    @ratelimit(group='lists', key='user', rate='100/h')
    def user_list(request):
        pass

    @ratelimit(group='lists', key='user', rate='100/h')
    def group_list(request):
        pass

You can also stack multiple decorators with different sets of applicable
methods::

    @ratelimit(key='ip', method='GET', rate='1000/h')
    @ratelimit(key='ip', method='POST', rate='100/h')
    def maybe_expensive(request):
        pass

This allows a total of 1,100 requests to this view in one hour, while
this would only allow 1000, but still only 100 POSTs::

    @ratelimit(key='ip', method=['GET', 'POST'], rate='1000/h')
    @ratelimit(key='ip', method='POST', rate='100/h')
    def maybe_expensive(request):
        pass

And these two decorators would not share a rate limit::

    @ratelimit(key='ip', method=['GET', 'POST'], rate='100/h')
    def foo(request):
        pass

    @ratelimit(key='ip', method='GET', rate='100/h')
    def bar(request):
        pass

But these two do share a rate limit::

    @ratelimit(group='a', key='ip', method=['GET', 'POST'], rate='1/s')
    def foo(request):
        pass

    @ratelimit(group='a', key='ip', method=['POST', 'GET'], rate='1/s')
    def bar(request):
        pass


Using multiple decorators
-------------------------

A single ``@ratelimit`` decorator used to be able to ratelimit against
multiple keys, e.g., before 0.5::

    @ratelimit(ip=True, field='username', keys=mykeysfunc)
    def someview(request):
        # ...

To simplify both the internals and the question of what limits apply,
each decorator now tracks exactly one rate, but decorators can be more
reliably stacked (c.f. some examples in the section above).

The pre-0.5 example above would need to become four decorators::

    @ratelimit(key='ip')
    @ratelimit(key='post:username')
    @ratelimit(key='get:username')
    @ratelimit(key=mykeysfunc)
    def someview(request):
        # ...

As documented above, however, this allows powerful new uses, like burst
limits and distinct GET/POST limits.


.. _least-surprising: http://en.wikipedia.org/wiki/Principle_of_least_astonishment
