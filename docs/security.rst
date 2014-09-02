.. _security-chapter:

=======================
Security considerations
=======================


Client IP address
=================

IP address is an extremely common rate limit :ref:`key <keys-chapter>`,
so it is important to configure correctly, especially in the
equally-common case where Django is behind a load balancer or other
reverse proxy.

Django-Ratelimit is **not** the correct place to handle reverse proxies
and adjust the IP address, and patches dealing with it will not be
accepted. There is `too much variation`_ in the wild to handle it
safely.

This is the same reason `Django dropped`_
``SetRemoteAddrFromForwardedFor`` middleware in 1.1: no such "mechanism
can be made reliable enough for general-purpose use" and it "may lead
developers to assume that the value of ``REMOTE_ADDR`` is 'safe'."


Risks
-----

Mishandling client IP data creates an IP spoofing vector that allows
attackers to circumvent IP ratelimiting entirely. Consider an attacker
with the real IP address 3.3.3.3 that adds the following to a request::

    X-Forwarded-For: 1.2.3.4

A misconfigured web server may pass the header value along, e.g.::

    X-Forwarded-For: 3.3.3.3, 1.2.3.4

Alternatively, if the web server sends a different header, like
``X-Cluster-Client-IP`` or  ``X-Real-IP``, and passes along the
spoofed ``X-Forwarded-For`` header unchanged, a mistake in ratelimit or
a misconfiguration in Django could read the spoofed header instead of
the intended one.


Remediation
-----------

There are two options, configuring django-ratelimit or adding global
middleware. Which makes sense depends on your setup.


Middleware
^^^^^^^^^^

Writing a small middleware class to set ``REMOTE_ADDR`` to the actual
client IP address is generally simple::

    class ReverseProxy(object):
        def process_request(self, request):
            request.META['REMOTE_ADDR'] = # [...]

where ``# [...]`` depends on your environment. This middleware should be
close to the top of the list::

    MIDDLEWARE_CLASSES = (
        'path.to.ReverseProxy',
        # ...
    )

Then the ``@ratelimit`` decorator can be used with the ``ip`` key::

    @ratelimit(key='ip', rate='10/s')

Ratelimit keys
^^^^^^^^^^^^^^

Alternatively, if the client IP address is in a simple header (i.e. a
header like ``X-Real-IP`` that *only* contains the client IP, unlike
``X-Forwarded-For`` which may contain intermediate proxies) you can use
a ``header:`` key::

    @ratelimit(key='header:x-real-ip', rate='10/s')

.. _too much variation: http://www.wikiwand.com/en/Talk:X-Forwarded-For#Variations
.. _Django dropped: https://docs.djangoproject.com/en/1.3/releases/1.1/#removed-setremoteaddrfromforwardedfor-middleware
