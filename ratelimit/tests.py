import time
from django.core.cache import cache
from django.test import RequestFactory

from nose.tools import with_setup

from ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited


class assert_raises(object):
    """A context manager that asserts a given exception was raised.

    >>> with assert_raises(TypeError):
    ...     raise TypeError

    >>> with assert_raises(TypeError):
    ...     raise ValueError
    AssertionError: 'ValueError' not in ['TypeError']

    >>> with assert_raises(TypeError):
    ...     pass
    AssertionError: No exception raised.

    Or you can specify any of a number of exceptions:

    >>> with assert_raises(TypeError, ValueError):
    ...     raise ValueError

    >>> with assert_raises(TypeError, ValueError):
    ...     raise KeyError
    AssertionError: 'KeyError' not in ['TypeError', 'ValueError']

    You can also get the exception back later:

    >>> with assert_raises(TypeError) as cm:
    ...     raise TypeError('bad type!')
    >>> cm.exception
    TypeError('bad type!')
    >>> cm.exc_type
    TypeError
    >>> cm.traceback
    <traceback @ 0x3323ef0>

    Lowercase name because that it's a class is an implementation detail.

    """

    def __init__(self, *exc_cls):
        self._exc_cls = exc_cls

    def __enter__(self):
        # For access to the exception later.
        return self

    def __exit__(self, typ, value, tb):
        assert typ, 'No exception raised.'
        assert typ in self._exc_cls, "'%s' not in %s" % (
            typ.__name__, [e.__name__ for e in self._exc_cls])
        self.exc_type = typ
        self.exception = value
        self.traceback = tb

        # Swallow expected exceptions.
        return True


def setup():
    cache.clear()


@with_setup(setup)
def test_limit_ip():
    @ratelimit(ip=True, method=None, rate='1/m', block=True)
    def view(request):
        return True

    req = RequestFactory().get('/')
    with assert_raises(Ratelimited):
        assert view(req)
        view(req)


@with_setup(setup)
def test_limit_ip_use():
    @ratelimit(ip=True, method=None, rate='1/m', block=True, use='ratelimit')
    def view(request):
        return True

    req = RequestFactory().get('/')
    with assert_raises(Ratelimited):
        assert view(req)
        view(req)


@with_setup(setup)
def test_block():
    @ratelimit(ip=True, method=None, rate='1/m', block=True)
    def blocked(request):
        return True

    @ratelimit(ip=True, method=None, rate='1/m', block=False)
    def unblocked(request):
        return request.limited

    req = RequestFactory().get('/')

    with assert_raises(Ratelimited):
        assert blocked(req)
        blocked(req)

    assert unblocked(req)


@with_setup(setup)
def test_method():
    rf = RequestFactory()
    post = rf.post('/')
    get = rf.get('/')

    @ratelimit(ip=True, method=['POST'], rate='1/m')
    def limit_post(request):
        return request.limited

    @ratelimit(ip=True, method=['POST', 'GET'], rate='1/m')
    def limit_get(request):
        return request.limited

    assert not limit_post(post)
    assert limit_post(post)
    assert not limit_post(get)
    assert limit_get(post)
    assert limit_get(get)


@with_setup(setup)
def test_field():
    james = RequestFactory().post('/', {'username': 'james'})
    john = RequestFactory().post('/', {'username': 'john'})

    @ratelimit(ip=False, field='username', rate='1/m')
    def username(request):
        return request.limited

    assert not username(james)
    assert username(james)
    assert not username(john)


@with_setup(setup)
def test_field_unicode():
    post = RequestFactory().post('/', {'username': u'fran\xe7ois'})

    @ratelimit(ip=False, field='username', rate='1/m')
    def view(request):
        return request.limited

    assert not view(post)
    assert view(post)


@with_setup(setup)
def test_field_empty():
    post = RequestFactory().post('/', {})

    @ratelimit(ip=False, field='username', rate='1/m')
    def view(request):
        return request.limited

    assert not view(post)
    assert view(post)


@with_setup(setup)
def test_rate():
    req = RequestFactory().post('/')

    @ratelimit(ip=True, rate='2/m')
    def twice(request):
        return request.limited

    assert not twice(req)
    assert not twice(req)
    assert twice(req)


@with_setup(setup)
def test_skip_if():
    req = RequestFactory().post('/')

    @ratelimit(rate='1/m', skip_if=lambda r: getattr(r, 'skip', False))
    def view(request):
        return request.limited

    assert not view(req)
    assert view(req)
    req.skip = True
    assert not view(req)


@with_setup(setup)
def test_limit_ip_minute_later():
    @ratelimit(ip=True, method=None, rate='1/m', block=True)
    def view(request):
        return True

    req = RequestFactory().get('/')
    with assert_raises(Ratelimited):
        assert view(req)
        view(req)

    #time.sleep(60)
    with assert_raises(Ratelimited):
        assert view(req)
        view(req)
    
