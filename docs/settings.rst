.. _settings-chapter:

========
Settings
========

``RATELIMIT_CACHE_PREFIX``:
    An optional cache prefix for ratelimit keys (in addition to the
    ``PREFIX`` value). *rl:*
``RATELIMIT_ENABLE``:
    Set to ``False`` to disable rate-limiting across the board. *True*
``RATELIMIT_USE_CACHE``:
    Which cache (from the ``CACHES`` dict) to use. *default*
``RATELIMIT_VIEW``:
    A view to use when a request is ratelimited, in conjunction with
    ``RatelimitMiddleware``. (E.g.: ``'myapp.views.ratelimited'``.)
    *None*
