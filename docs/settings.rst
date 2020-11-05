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

``RATELIMIT_IPV4_MASK``
-----------------------

IPv4 mask for IP-based rate limit. Defaults to ``32`` (which is no masking)

``RATELIMIT_IPV6_MASK``
-----------------------

IPv6 mask for IP-based rate limit. Defaults to ``64`` (which mask the last 64 bits).
Typical end site IPv6 assignment are from /48 to /64.

``RATELIMIT_RECORD``
--------------------

Whether to record exceeded limits to a cache or database backend. Defaults to ``False``

``RATELIMIT_RECORD_HANDLER``
----------------------------

If you have set ``RATELIMIT_RECORD`` to ``True`` you can also provide an optional handler value 
with ``RATELIMIT_RECORD_HANDLER`` setting to define whether the exceeded limits get recorded to cache, 
or database backend. There are trade offs, cache backend is fast and doesn't become a bottleneck for performance,
but it isn't as secure as a database backend. Using a database backend could be an expensive,
but more secure way to record your logs depending on your throughput.

Defaults to ``ratelimit.record_handlers.database.DatabaseRecordHandler``

- ``ratelimit.record_handlers.database.DatabaseRecordHandler``

- ``ratelimit.record_handlers.cache.CacheRecordHandler``

You should provide one of the above as a string , e.g.  

.. code-block:: python

    RATELIMIT_RECORD_HANDLER = "ratelimit.record_handlers.cache.CacheRecordHandler"

``RATELIMIT_ENABLE_ADMIN``
--------------------------

If you want to disable admin panel for ratelimit records you can set this setting to ``False``.
Defaults to ``True``

``RATELIMIT_CACHE_RECORD_TIME``
-------------------------------

When you're recording your logs in cache, you can provide an optional value to this setting to
purge the data in cache automatically.
Can be set to a Python timedelta object, an integer, a callable, 
or a string path to a callable which takes no arguments. The integers are interpreted as hours.
Defaults to six days.