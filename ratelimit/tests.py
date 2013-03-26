from django.core.cache import cache, InvalidCacheBackendError
from django.test import RequestFactory, TestCase
try:
    from django.test.utils import override_settings
except ImportError:
    from override_settings import override_settings

from ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited


class RatelimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_limit_ip(self):
        @ratelimit(ip=True, method=None, rate='1/m', block=True)
        def view(request):
            return True

        req = RequestFactory().get('/')
        assert view(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            view(req)

    def test_block(self):
        @ratelimit(ip=True, method=None, rate='1/m', block=True)
        def blocked(request):
            return request.limited

        @ratelimit(ip=True, method=None, rate='1/m', block=False)
        def unblocked(request):
            return request.limited

        req = RequestFactory().get('/')

        assert not blocked(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            blocked(req)

        assert unblocked(req), 'Request is limited but not blocked.'

    def test_method(self):
        rf = RequestFactory()
        post = rf.post('/')
        get = rf.get('/')

        @ratelimit(ip=True, method=['POST'], rate='1/m')
        def limit_post(request):
            return request.limited

        @ratelimit(ip=True, method=['POST', 'GET'], rate='1/m')
        def limit_get(request):
            return request.limited

        assert not limit_post(post), 'Do not limit first POST.'
        assert limit_post(post), 'Limit second POST.'
        assert not limit_post(get), 'Do not limit GET.'

        assert limit_get(post), 'Limit first POST.'
        assert limit_get(get), 'Limit first GET.'

    def test_field(self):
        james = RequestFactory().post('/', {'username': 'james'})
        john = RequestFactory().post('/', {'username': 'john'})

        @ratelimit(ip=False, field='username', rate='1/m')
        def username(request):
            return request.limited

        assert not username(james), "james' first request is fine."
        assert username(james), "james' second request is limited."
        assert not username(john), "john's first request is fine."

    def test_field_unicode(self):
        post = RequestFactory().post('/', {'username': u'fran\xe7ois'})

        @ratelimit(ip=False, field='username', rate='1/m')
        def view(request):
            return request.limited

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_field_empty(self):
        post = RequestFactory().post('/', {})

        @ratelimit(ip=False, field='username', rate='1/m')
        def view(request):
            return request.limited

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_rate(self):
        req = RequestFactory().post('/')

        @ratelimit(ip=True, rate='2/m')
        def twice(request):
            return request.limited

        assert not twice(req), 'First request is not limited.'
        assert not twice(req), 'Second request is not limited.'
        assert twice(req), 'Third request is limited.'

    def test_skip_if(self):
        req = RequestFactory().post('/')

        @ratelimit(rate='1/m', skip_if=lambda r: getattr(r, 'skip', False))
        def view(request):
            return request.limited

        assert not view(req), 'First request is not limited.'
        assert view(req), 'Second request is limited.'
        req.skip = True
        assert not view(req), 'Skipped request is not limited.'

    @override_settings(RATELIMIT_USE_CACHE='fake.cache')
    def test_bad_cache(self):
        """The RATELIMIT_USE_CACHE setting works if the cache exists."""

        @ratelimit()
        def view(request):
            return request

        req = RequestFactory().post('/')

        with self.assertRaises(InvalidCacheBackendError):
            view(req)

    def test_keys(self):
        """Allow custom functions to set cache keys."""
        class User(object):
            def __init__(self, authenticated=False):
                self.pk = 1
                self.authenticated = authenticated

            def is_authenticated(self):
                return self.authenticated

        def user_or_ip(req):
            if req.user.is_authenticated():
                return 'uip:%d' % req.user.pk
            return 'uip:%s' % req.META['REMOTE_ADDR']

        @ratelimit(ip=False, rate='1/m', block=False, keys=user_or_ip)
        def view(request):
            return request.limited

        req = RequestFactory().post('/')
        req.user = User(authenticated=False)

        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

        req.user = User(authenticated=True)

        assert not view(req), 'First authenticated request is allowed.'
        assert view(req), 'Second authenticated is limited.'
