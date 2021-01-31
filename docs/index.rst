================
Django Ratelimit
================

Project
=======

**Django Ratelimit** is a ratelimiting decorator for Django views,
storing rate data in the configured `Django cache backend
<https://docs.djangoproject.com/en/dev/topics/cache/>`__.

.. image:: https://travis-ci.org/jsocol/django-ratelimit.png?branch=master
   :target: https://travis-ci.org/jsocol/django-ratelimit

:Code:          https://github.com/jsocol/django-ratelimit
:License:       Apache Software License
:Issues:        https://github.com/jsocol/django-ratelimit/issues
:Documentation: http://django-ratelimit.readthedocs.org/


Quickstart
==========

Install:

.. code-block:: shell

   $ pip install django-ratelimit


Use as a decorator in ``views.py``:

.. code-block:: python

    from django_ratelimit.decorators import ratelimit

    @ratelimit(key='ip')
    def myview(request):
        # ...

    @ratelimit(key='ip', rate='100/h')
    def secondview(request):
        # ...

After activating django-ratelimit, you should ensure that your cache
backend is setup to be both persistent and work across multiple
deployment worker instances (for instance UWSGI workers). Read more in
the Django docs on `caching
<https://docs.djangoproject.com/en/dev/topics/cache/>`__.

.. _PyPI: http://pypi.python.org/pypi/django-ratelimit


Contents
========

.. toctree::
   :maxdepth: 2

   settings
   usage
   keys
   rates
   security
   upgrading
   contributing
   cookbook/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

