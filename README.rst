================
Django Ratelimit
================

Django Ratelimit provides a decorator to rate-limit views. Limiting can
be based on IP address or a field in the request--either a GET or POST
variable.

.. image:: https://github.com/jsocol/django-ratelimit/workflows/test/badge.svg?branch=main
   :target: https://github.com/jsocol/django-ratelimit/actions

:Code:          https://github.com/jsocol/django-ratelimit
:License:       Apache Software License 2.0; see LICENSE file
:Issues:        https://github.com/jsocol/django-ratelimit/issues
:Documentation: http://django-ratelimit.readthedocs.io/

**Note** This part of the documentation is not included in the above link, so check below.   

    
``Documentation specific to the ratelimit-recorder``
------
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
