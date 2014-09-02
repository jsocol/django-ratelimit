.. _rates-chapter:

=====
Rates
=====


.. _rates-simple:

Simple rates
============

Simple rates are of the form ``X/u`` where ``X`` is a number of requests
and ``u`` is a unit from this list:

* ``s`` - second
* ``m`` - minute
* ``h`` - hour
* ``d`` - day

(For example, you can read ``5/s`` as "five per second.")

You may also specify a number of units, i.e.: ``X/Yu`` where ``Y`` is a
number of units. If ``u`` is omitted, it is presumed to be seconds. So,
the following are equivalent, and all mean "one hundred requests per
five minutes":

* ``100/5m``
* ``100/300s``
* ``100/300``


.. _rates-callable:

Callables
=========

Rates can also be callables (or dotted paths to callables, which are
assumed if there is no ``/`` in the value).


Callables receive two values, the :ref:`group <usage-chapter>` and the
``request`` object. They should return a simple rate string, or a tuple
of integers ``(count, seconds)``. For example::

    def my_rate(group, request):
        if request.user.is_authenticated():
            return '1000/m'
        return '100/m'

Or equivalently::

    def my_rate_tuples(group, request):
        if request.user.is_authenticated():
            return (1000, 60)
        return (100, 60)

Callables can return ``0`` in the first place to disallow any requests
(e.g.: ``0/s``, ``(0, 60)``). They can return ``None`` for "no
ratelimit".
