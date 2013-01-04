.. _install-chapter:

===========================
Installing Django Ratelimit
===========================

Just install from PyPI_ or GitHub_ and start using_::

    pip install django-ratelimit


::

    from ratelimit.decorators import ratelimit

    @ratelimit()
    def myview(request):
        # ...


.. _PyPI: http://pypi.python.org/pypi/django-ratelimit
.. _GitHub: https://github.com/jsocol/django-ratelimit
.. _using: usage-chapter
