.. _settings-chapter:

========
Settings
========

``RATELIMIT_ENABLE``:
    Set to ``False`` to disable rate-limiting across the board. *True*
``RATELIMIT_VIEW``:
    A view to use when a request is ratelimited, in conjunction with
    ``RatelimitMiddleware``. (E.g.: ``'myapp.views.ratelimited'``.) *None*
