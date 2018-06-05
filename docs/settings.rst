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
------------------

Whether to allow requests when the cache backend fails. Defaults to ``False``.
