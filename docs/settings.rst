.. _settings-chapter:

========
Settings
========

``RATELIMIT_CACHE_PREFIX``
--------------------------

An optional cache prefix for ratelimit keys (in addition to the ``PREFIX``
value defined on the cache backend). Defaults to ``'rl:'``.

``RATELIMIT_ENABLE``
--------------------

Set to ``False`` to disable rate-limiting across the board. Defaults to
``True``.

May be useful during tests with Django's |override_settings|_ testing tool,
for example:

.. code-block:: python

    from django.test import override_settings

    with override_settings(RATELIMIT_ENABLE=False):
        result = call_the_view()

.. |override_settings| replace:: ``override_settings()``
.. _override_settings: https://docs.djangoproject.com/en/2.0/topics/testing/tools/#django.test.override_settings.

``RATELIMIT_USE_CACHE``
-----------------------

.. warning::
   `django_ratelimit` requires a Django cache backend that supports _`atomic
   increment` operations. The Memcached and Redis backends do, but the database
   backend does not.

The name of the cache (from the ``CACHES`` dict) to use. Defaults to
``'default'``.

``RATELIMIT_VIEW``
------------------

The string import path to a view to use when a request is ratelimited, in
conjunction with ``RatelimitMiddleware``, e.g. ``'myapp.views.ratelimited'``.
Has no default - you must set this to use ``RatelimitMiddleware``.

``RATELIMIT_FAIL_OPEN``
-----------------------

Whether to allow requests when the cache backend fails. Defaults to ``False``.

``RATELIMIT_IP_META_KEY``
-------------------------

Set the source of the client IP address in the request.META object. Defaults to
``None``.

There are several potential values:

``None``
  Use ``request.META['REMOTE_ADDR']`` as the source of the client IP address.

A callable object
  If set to a callable, the callable will be passed the full ``request``
  object. The callable must return the client IP address. For example:
  ``RATELIMIT_IP_META_KEY = lambda r: r.META['HTTP_X_CLIENT_IP']``

A dotted path to a callable
  Any string containing a ``.`` will be treated as a dotted path to a callable,
  which will be imported and called on the ``request`` object, as above.

Any other string
  Any other string will be treated as a key for the ``request.META`` object,
  e.g. ``RATELIMIT_IP_META_KEY = 'HTTP_X_REAL_IP'``

``RATELIMIT_IPV4_MASK``
-----------------------

IPv4 mask for IP-based rate limit. Defaults to ``32`` (which is no masking)

``RATELIMIT_IPV6_MASK``
-----------------------

IPv6 mask for IP-based rate limit. Defaults to ``64`` (which mask the last 64 bits).
Typical end site IPv6 assignment are from /48 to /64.
