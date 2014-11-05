============
Contributing
============


For set up, tests, and code standards, see `the documentation`_.


Client IP Address
=================

Because this comes up frequently:

I will not accept a  pull request or issue attempting to handle client
IP address when Django is behind a proxy.

*Ratelimit is the wrong place for this.* There are more details in the
`security chapter`_ of the documentation.


.. _the documentation: https://django-ratelimit.readthedocs.org/en/latest/contributing.html
.. _security chapter: https://django-ratelimit.readthedocs.org/en/latest/security.html#client-ip-address
