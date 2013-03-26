.. _contributing-chapter:

============
Contributing
============


Set Up
======

Create a virtualenv_ and install Django with pip_::

    pip install Django


Running the Tests
=================

Running the tests is as easy as::

    $ ./run.sh test

You may also run the test on multiple versions of Django::

    $ tox


Code Standards
==============

I ask two things for pull requests.

* The flake8_ tool must not report any violations.
* All tests, including new tests where appropriate, must pass.


.. _virtualenv: http://www.virtualenv.org/en/latest/
.. _pip: http://www.pip-installer.org/en/latest/
.. _flake8: https://pypi.python.org/pypi/flake8
