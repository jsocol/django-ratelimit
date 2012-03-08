================
Django Ratelimit
================

Django Ratelimit provides a decorator to rate-limit views. Limiting can be
based on IP address or a field in the request--either a GET or POST variable.

If the rate limit is exceded, either a 403 Forbidden can be sent, or the
request can be annotated with a ``limited`` attribute, allowing you to take
another action like adding a captcha to a form.


Using Django Ratelimit
======================

``from ratelimit.decorators import ratelimit`` is the biggest thing you need to
do. The ``@ratelimit`` decorator provides several optional arguments with
sensible defaults:

:``ip``:
    Whether to rate-limit based on the IP.
    *Default: True*
:``block``:
    Whether to block the request instead of annotating. 
    *Default: False*
:``method``:
    Which HTTP method(s) to rate-limit. May be a string or a list.
    *Default: all*
:``field``:
    Which HTTP field(s) to use to rate-limit. May be a string or a list.
    *Default: none*
:``rate``:
    The number of requests per unit time allowed.
    *Default: 5/m*
:``skip_if``:
    If specified, pass this parameter a callable (e.g. lambda function) that takes the current request. If the callable returns a value that evaluates to True, the rate limiting is skipped for that particular view. This is useful to do things like selectively deactivating rate limiting based on a value in your settings file, or based on an attirbute in the current request object. (Also see the ``RATELIMIT_DISABLE_ALL`` settings option below.)
    *Default: None*


In addition, you may choose to configure any of the following variables in your Django settings file:

:``RATELIMIT_DISABLE_ALL``:
    Set to True to disable rate-limiting across the board.
    *Default: False*


Examples
--------

::

    @ratelimit()
    def myview(request):
        # Will be true if the same IP makes more than 5 requests/minute.
        was_limited = getattr(request, 'limited', False)
        return HttpResponse()

    @ratelimit(block=True)
    def myview(request):
        # If the same IP makes >5 reqs/min, will return HttpResponseForbidden
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


Acknowledgements
================

I would be remiss not to mention `Simon Willison`_'s ratelimitcache_, on which
this is largely based.

.. _Simon Willison: http://simonwillison.net/
.. _ratelimitcache: https://github.com/simonw/ratelimitcache
