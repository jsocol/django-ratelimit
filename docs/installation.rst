.. _installation-chapter:

============
Installation
============

.. _installation-cache:

Create or use a compatible cache
================================

``django_ratelimit`` requires a cache backend that

#. Is shared across any worker threads, processes, and application servers.
   Cache backends that use sharding can be used to help scale this.
#. Implements *atomic increment*.

`Redis`_ and `Memcached`_ backends have these features and are officially supported.
Backends like `local memory`_ and `filesystem`_ are not shared across processes
or servers. Notably, the `database`_ backend does **not** support atomic
increments.

If you do not have a compatible cache backend, you'll need to set one up, which
is out of scope of this document, and then add it to the ``CACHES`` dictionary
in `settings`_.

.. warning::
   Without atomic increment operations, ``django_ratelimit`` will appear to
   work, but there is a race condition between reading and writing usage count
   data that can result in undercounting usage and permitting more traffic than
   intended.

.. _Redis: https://docs.djangoproject.com/en/4.1/topics/cache/#redis
.. _Memcached: https://docs.djangoproject.com/en/4.1/topics/cache/#memcached
.. _local memory: https://docs.djangoproject.com/en/4.1/topics/cache/#local-memory-caching
.. _filesystem: https://docs.djangoproject.com/en/4.1/topics/cache/#filesystem-caching
.. _database: https://docs.djangoproject.com/en/4.1/topics/cache/#database-caching
.. _settings: https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-CACHES


.. _installation-settings:

Configuration
=============

``django_ratelimit`` has reasonable defaults, and if your ``default`` cache is
compatible, and your application is not behind a reverse proxy, you can skip
this section.

For a complete list of configuration options, see :ref:`Settings
<settings-chapter>`.

.. _installation-settings-cache:

Cache Settings
--------------

If you have added an additional ``CACHES`` entry for ratelimiting, you'll need
to tell ``django_ratelimit`` to use this via the ``RATELIMIT_USE_CACHE``
setting:

.. code-block:: python

    # your_apps_settings.py
    CACHES = {
        'default': {},
        'cache-for-ratelimiting': {},
    }

    RATELIMIT_USE_CACHE = 'cache-for-ratelimiting'

.. _installation-settings-ip:

Reverse Proxies and Client IP Address
-------------------------------------

``django_ratelimit`` reads client IP address from
``request.META['REMOTE_ADDR']``. If your application is running behind a
reverse proxy such as nginx or HAProxy, you will need to take steps to ensure
you have access to the correct client IP address, rather than the address of
the proxy.

There are security risks for libraries to *assume* how your network is set up,
and so ``django_ratelimit`` does not provide any built-in tools to address
this. However, the :ref:`Security chapter <security-client-ip>` does provide
suggestions on how to approach this.


.. _installation-enforcing:

Enforcing Ratelimits
====================

The most common way to enforce ratelimits is via the ``ratelimit``
:ref:`decorator <usage-decorator>`:

.. code-block:: python

    from django_ratelimit.decorators import ratelimit

    @ratelimit(key='user_or_ip', rate='10/m')
    def myview(request):
        # limited to 10 req/minute for a given user or client IP

    # or on class methods
    class MyView(View):
        @method_decorator(ratelimit(key='user_or_ip', rate='1/s'))
        def get(self, request):
            # limited to 1 req/second
