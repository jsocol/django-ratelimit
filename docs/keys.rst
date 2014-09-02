.. _keys-chapter:

==============
Ratelimit Keys
==============

The ``key=`` argument to the decorator takes either a string or a
callable.


.. _keys-common:

Common keys
===========

The following string values for ``key=`` provide shortcuts to commonly
used ratelimit keys:

* ``'ip'`` - Use the request IP address (i.e.
  ``request.META['REMOTE_ADDR']``)
  
    .. note::
       If you are using a reverse proxy, make sure this value is correct
       or use an appropriate ``header:`` value. See the :ref:`security
       <security-chapter>` notes.
* ``'get:X'`` - Use the value of ``request.GET['X']``.
* ``'post:X'`` - Use the value of ``request.POST['X']``.
* ``'field:X'`` - Use ``request.POST['X']`` if the request method is
  ``POST``, otherwise use ``request.GET['X']``.
* ``'header:x-x'`` - Use the value of ``request.META['HTTP_X_X']``.
  
    .. note::
       The value right of the colon will be translated to all-caps and
       any dashes will be replaced with underscores, e.g.: x-client-ip
       => X_CLIENT_IP.
* ``'user'`` - Use an appropriate value from ``request.user``. Do not use
  with unauthenticated users.
* ``'user_or_ip'`` - Use an appropriate value from ``request.user`` if
  the user is authenticated, otherwise use
  ``request.META['REMOTE_ADDR']`` (see the note above about reverse
  proxies).


.. _keys-strings:

String values
=============

Other string values not from the list above will be treated as the
dotted Python path to a callable. See :ref:`below <keys-callable>` for
more on callables.


.. _keys-callable:

Callable values
===============

If the value of ``key=`` is a callable, or the path to a callable, that
callable will be called with two arguments, the :ref:`group
<usage-chapter>` and the ``request`` object. It should return a
bytestring or unicode object, e.g.::

    def my_key(group, request):
        return request.META['REMOTE_ADDR'] + request.user.username
