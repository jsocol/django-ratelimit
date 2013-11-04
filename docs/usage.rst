.. _usage-chapter:

======================
Using Django Ratelimit
======================


Use as a decorator
==================

The ``@ratelimit`` view decorator provides several optional arguments
with sensible defaults (in italics).

Import::

    from ratelimit.decorators import ratelimit


.. py:decorator:: ratelimit(ip=True, block=False, method=None, field=None, rate='5/m', skip_if=None, keys=None)

   :arg ip:
       *True* Whether to rate-limit based on the IP from ``REMOTE_ADDR``.

       .. Note::

          If you're using a reverse proxy, set this to False and use
          the ``keys`` argument.

   :arg block:
       *False* Whether to block the request instead of annotating.

   :arg method:
        *None* Which HTTP method(s) to rate-limit. May be a string, a
        list/tuple, or ``None`` for all methods.

   :arg field:
        *None* Which HTTP GET/POST argument field(s) to use to
        rate-limit. May be a string or a list of strings.

   :arg rate:
        *'5/m'* The number of requests per unit time allowed. Valid units are:

        * ``s`` - seconds
        * ``m`` - minutes
        * ``h`` - hours
        * ``d`` - days

   :arg skip_if:
        *None* If specified, pass this parameter a callable
        (e.g. lambda function) that takes the current request. If the
        callable returns a value that evaluates to True, the rate
        limiting is skipped for that particular view. This is useful
        to do things like selectively deactivating rate limiting based
        on a value in your settings file, or based on an attirbute in
        the current request object. (Also see the ``RATELIMIT_ENABLE``
        setting below.)

   :arg keys:
        *None* Specify a function or list of functions that take the
        request object and return string keys. This allows you to
        define custom logic (for example, use an authenticated user ID
        or unauthenticated IP address).

        .. Note::

           If you're using a reverse proxy, pass in a function that
           pulls the appropriate field from ``request.META`` for the
           actual ip address of the client.


Examples::

    @ratelimit()
    def myview(request):
        # Will be true if the same IP makes more than 5 requests/minute.
        was_limited = getattr(request, 'limited', False)
        return HttpResponse()

    @ratelimit(block=True)
    def myview(request):
        # If the same IP makes >5 reqs/min, will raise Ratelimited
        return HttpResponse()

    @ratelimit(field='username')
    def login(request):
        # If the same username OR IP is used >5 times/min, this will be True.
        # The `username` value will come from GET or POST, determined by the
        # request method.
        was_limited = getattr(request, 'limited', False)
        return HttpResponse()

    @ratelimit(method='POST')
    def login(request):
        # Only apply rate-limiting to POSTs.
        return HttpResponseRedirect()

    @ratelimit(field=['username', 'other_field'])
    def login(request):
        # Use multiple field values.
        return HttpResponse()

    @ratelimit(rate='4/h')
    def slow(request):
        # Allow 4 reqs/hour.
        return HttpResponse()

    @ratelimit(skip_if=lambda request: getattr(request, 'some_attribute', False))
    def skipif1(request):
        # Conditionally skip rate limiting (example 1)
        return HttpResponse()

    @ratelimit(skip_if=lambda request: settings.MYAPP_DEACTIVATE_RATE_LIMITING)
    def skipif2(request):
        # Conditionally skip rate limiting (example 2)
        return HttpResponse()

    @ratelimit(keys=lambda x: 'min', rate='1/m')
    @ratelimit(keys=lambda x: 'hour', rate='10/h')
    @ratelimit(keys=lambda x: 'day', rate='50/d')
    def post(request):
        # Stack them.
        # Note: once a decorator limits the request, the ones after
        # won't count the request for limiting.
        return HttpResponse()

    @ratelimit(ip=False,
               keys=lambda req: req.META.get('HTTP_X_CLUSTER_CLIENT_IP',
                                             req.META['REMOTE_ADDR']))
    def post(request):
        # This will use the HTTP_X_CLUSTER_CLIENT_IP and default to
        # REMOTE_ADDR if that's not set. This is how you'd set up your
        # rate limiting if you're behind a reverse proxy.
        #
        # It's important to set ip to False here. Otherwise it'll use
        # limit on EITHER HTTP_X_CLUSTER_CLIENT_IP or REMOTE_ADDR and
        # the end result is that everything will be throttled.
        return HttpResponse()


Helper Function
===============

In some cases the decorator is not flexible enough. If this is an
issue you use the ``is_ratelimited`` helper function. It's similar to
the decorator.

Import::

    from ratelimit.helpers import is_ratelimited


.. py:function:: is_ratelimited(request, increment=False, ip=True, method=None, field=None, rate='5/m', keys=None)

   :arg request:
       (Required) The request object.

   :arg increment:
       *False* Whether to increment the count.

   :arg ip:
       *True* Whether to rate-limit based on the IP.

   :arg method:
       *None* Which HTTP method(s) to rate-limit. May be a string, a
       list/tuple, or ``None`` for all methods.

   :arg field:
       *None* Which HTTP field(s) to use to rate-limit. May be a
       string or a list.

   :arg rate:
       *'5/m'* The number of requests per unit time allowed.

   :arg keys:
       *None* Specify a function or list of functions that take the
       request object and return string keys. This allows you to
       define custom logic (for example, use an authenticated user ID
       or unauthenticated IP address).


Exceptions
==========

.. py:class:: ratelimit.exceptions.Ratelimited

   If a request is ratelimited and ``block`` is set to ``True``,
   Ratelimit will raise ``ratelimit.exceptions.Ratelimited``.

   This is a subclass of Django's ``PermissionDenied`` exception, so
   if you don't need any special handling beyond the built-in 403
   processing, you don't have to do anything.


Middleware
==========

There is optional middleware to use a custom view to handle ``Ratelimited``
exceptions.

To use it, add ``ratelimit.middleware.RatelimitMiddleware`` to your
``MIDDLEWARE_CLASSES`` (toward the bottom of the list) and set
``RATELIMIT_VIEW`` to the full path of a view you want to use.

The view specified in ``RATELIMIT_VIEW`` will get two arguments, the
``request`` object (after ratelimit processing) and the exception.
