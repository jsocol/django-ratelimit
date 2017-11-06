.. _usage-chapter:

======================
Using Django Ratelimit
======================


.. _usage-decorator:

Use as a decorator
==================

Import::

    from ratelimit.decorators import ratelimit


.. py:decorator:: ratelimit(group=None, key=, rate=None, method=ALL, block=False)

   :arg group:
       *None* A group of rate limits to count together. Defaults to the
       dotted name of the view.

   :arg key:
       What key to use, see :ref:`Keys <keys-chapter>`.

   :arg rate:
        *'5/m'* The number of requests per unit time allowed. Valid
        units are:

        * ``s`` - seconds
        * ``m`` - minutes
        * ``h`` - hours
        * ``d`` - days

        Also accepts callables. See :ref:`Rates <rates-chapter>`.

   :arg method:
        *ALL* Which HTTP method(s) to rate-limit. May be a string, a
        list/tuple of strings, or the special values for ``ALL`` or
        ``UNSAFE`` (which includes ``POST``, ``PUT``, ``DELETE`` and
        ``PATCH``).

   :arg block:
       *False* Whether to block the request instead of annotating.


HTTP Methods
------------

Each decorator can be limited to one or more HTTP methods. The
``method=`` argument accepts a method name (e.g. ``'GET'``) or a list or
tuple of strings (e.g. ``('GET', 'OPTIONS')``).

There are two special shortcuts values, both accessible from the
``ratelimit`` decorator, the ``RatelimitMixin`` class, or the
``is_ratelimited`` helper, as well as on the root ``ratelimit`` module::

    from ratelimit.decorators import ratelimit

    @ratelimit(key='ip', method=ratelimit.ALL)
    @ratelimit(key='ip', method=ratelimit.UNSAFE)
    def myview(request):
        pass

``ratelimit.ALL`` applies to all HTTP methods. ``ratelimit.UNSAFE``
is a shortcut for ``('POST', 'PUT', 'PATCH', 'DELETE')``.


Examples
--------


::

    @ratelimit(key='ip', rate='5/m')
    def myview(request):
        # Will be true if the same IP makes more than 5 POST
        # requests/minute.
        was_limited = getattr(request, 'limited', False)
        return HttpResponse()

    @ratelimit(key='ip', rate='5/m', block=True)
    def myview(request):
        # If the same IP makes >5 reqs/min, will raise Ratelimited
        return HttpResponse()

    @ratelimit(key='post:username', rate='5/m', method=['GET', 'POST'])
    def login(request):
        # If the same username is used >5 times/min, this will be True.
        # The `username` value will come from GET or POST, determined by the
        # request method.
        was_limited = getattr(request, 'limited', False)
        return HttpResponse()

    @ratelimit(key='post:username', rate='5/m')
    @ratelimit(key='post:password', rate='5/m')
    def login(request):
        # Use multiple keys by stacking decorators.
        return HttpResponse()

    @ratelimit(key='get:q', rate='5/m')
    @ratelimit(key='post:q', rate='5/m')
    def search(request):
        # These two decorators combine to form one rate limit: the same search
        # query can only be tried 5 times a minute, regardless of the request
        # method (GET or POST)
        return HttpResponse()

    @ratelimit(key='ip', rate='4/h')
    def slow(request):
        # Allow 4 reqs/hour.
        return HttpResponse()

    rate = lambda r: None if request.user.is_authenticated() else '100/h'
    @ratelimit(key='ip', rate=rate)
    def skipif1(request):
        # Only rate limit anonymous requests
        return HttpResponse()

    @ratelimit(key='user_or_ip', rate='10/s')
    @ratelimit(key='user_or_ip', rate='100/m')
    def burst_limit(request):
        # Implement a separate burst limit.
        return HttpResponse()

    @ratelimit(group='expensive', key='user_or_ip', rate='10/h')
    def expensive_view_a(request):
        return something_expensive()

    @ratelimit(group='expensive', key='user_or_ip', rate='10/h')
    def expensive_view_b(request):
        # Shares a counter with expensive_view_a
        return something_else_expensive()

    @ratelimit(key='header:x-cluster-client-ip')
    def post(request):
        # Uses the X-Cluster-Client-IP header value.
        return HttpResponse()

    @ratelimit(key=lambda r: r.META.get('HTTP_X_CLUSTER_CLIENT_IP',
                                        r.META['REMOTE_ADDR'])
    def myview(request):
        # Use `X-Cluster-Client-IP` but fall back to REMOTE_ADDR.
        return HttpResponse()


Class-Based Views
-----------------

.. versionadded:: 0.5

The ``@ratelimit`` decorator also works on class-based view methods,
though *make sure the ``method`` argument matches the decorator*::

    class MyView(View):
        @ratelimit(key='ip', method='POST')
        def post(self, request, *args):
            # Something expensive...

.. note::
   Unless given an explicit ``group`` argument, different methods of a
   class-based view will be limited separate.


.. _usage-mixin:

Class-Based View Mixin
======================

.. py:class:: ratelimit.mixins.RatelimitMixin

.. versionadded:: 0.4

Ratelimits can also be applied to class-based views with the
``ratelimit.mixins.RatelimitMixin`` mixin. They are configured via class
attributes that are the same as the :ref:`decorator <usage-decorator>`,
prefixed with ``ratelimit_``, e.g.::

    class MyView(RatelimitMixin, View):
        ratelimit_key = 'ip'
        ratelimit_rate = '10/m'
        ratelimit_block = False
        ratelimit_method = 'GET'

        def get(self, request, *args, **kwargs):
            # Calculate expensive report...

.. versionchanged:: 0.5
   The name of the mixin changed from ``RateLimitMixin`` to
   ``RatelimitMixin`` for consistency.


.. _usage-helper:

Helper Function
===============

In some cases the decorator is not flexible enough. If this is an
issue you use the ``is_ratelimited`` helper function. It's similar to
the decorator.

Import::

    from ratelimit.utils import is_ratelimited


.. py:function:: is_ratelimited(request, group=None, key=, rate=None, method=ALL, increment=False, delta=0)

   :arg request:
       *None* The HTTPRequest object.

   :arg group:
       *None* A group of rate limits to count together. Defaults to the
       dotted name of the view.

   :arg key:
       What key to use, see :ref:`Keys <keys-chapter>`.

   :arg rate:
       *'5/m'* The number of requests per unit time allowed. Valid
       units are:

       * ``s`` - seconds
       * ``m`` - minutes
       * ``h`` - hours
       * ``d`` - days

       Also accepts callables. See :ref:`Rates <rates-chapter>`.

   :arg method:
       *ALL* Which HTTP method(s) to rate-limit. May be a string, a
       list/tuple, or ``None`` for all methods.

   :arg increment:
       *False* Whether to increment the count or just check.

   :arg delta:
       *0* Add delta to value in the cache if *increment* is *True*.

.. _usage-exception:

Exceptions
==========

.. py:class:: ratelimit.exceptions.Ratelimited

   If a request is ratelimited and ``block`` is set to ``True``,
   Ratelimit will raise ``ratelimit.exceptions.Ratelimited``.

   This is a subclass of Django's ``PermissionDenied`` exception, so
   if you don't need any special handling beyond the built-in 403
   processing, you don't have to do anything.


.. _usage-middleware:

Middleware
==========

There is optional middleware to use a custom view to handle ``Ratelimited``
exceptions.

To use it, add ``ratelimit.middleware.RatelimitMiddleware`` to your
``MIDDLEWARE_CLASSES`` (toward the bottom of the list) and set
``RATELIMIT_VIEW`` to the full path of a view you want to use.

The view specified in ``RATELIMIT_VIEW`` will get two arguments, the
``request`` object (after ratelimit processing) and the exception.
