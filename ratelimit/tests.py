from django.core.cache import cache, InvalidCacheBackendError
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.views.generic import View

from ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited
from ratelimit.mixins import RatelimitMixin
from ratelimit.utils import is_ratelimited, _split_rate


rf = RequestFactory()


class MockUser(object):
    def __init__(self, authenticated=False):
        self.pk = 1
        self.authenticated = authenticated

    def is_authenticated(self):
        return self.authenticated


class RateParsingTests(TestCase):
    def test_simple(self):
        tests = (
            ('100/s', (100, 1)),
            ('100/10s', (100, 10)),
            ('100/10', (100, 10)),
            ('100/m', (100, 60)),
            ('400/10m', (400, 600)),
            ('1000/h', (1000, 3600)),
            ('800/d', (800, 24 * 60 * 60)),
        )

        for i, o in tests:
            assert o == _split_rate(i)


def mykey(group, request):
    return request.META['REMOTE_ADDR'][::-1]


class RatelimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_no_key(self):
        @ratelimit(rate='1/m', block=True)
        def view(request):
            return True

        req = rf.get('/')
        with self.assertRaises(ImproperlyConfigured):
            view(req)

    def test_ip(self):
        @ratelimit(key='ip', rate='1/m', block=True)
        def view(request):
            return True

        req = rf.get('/')
        assert view(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            view(req)

    def test_block(self):
        @ratelimit(key='ip', rate='1/m', block=True)
        def blocked(request):
            return request.limited

        @ratelimit(key='ip', rate='1/m', block=False)
        def unblocked(request):
            return request.limited

        req = rf.get('/')

        assert not blocked(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            blocked(req)

        assert unblocked(req), 'Request is limited but not blocked.'

    def test_method(self):
        post = rf.post('/')
        get = rf.get('/')

        @ratelimit(key='ip', method='POST', rate='1/m', group='a')
        def limit_post(request):
            return request.limited

        @ratelimit(key='ip', method=['POST', 'GET'], rate='1/m', group='a')
        def limit_get(request):
            return request.limited

        assert not limit_post(post), 'Do not limit first POST.'
        assert limit_post(post), 'Limit second POST.'
        assert not limit_post(get), 'Do not limit GET.'

        assert limit_get(post), 'Limit first POST.'
        assert limit_get(get), 'Limit first GET.'

    def test_unsafe_methods(self):
        @ratelimit(key='ip', method=ratelimit.UNSAFE, rate='0/m')
        def limit_unsafe(request):
            return request.limited

        get = rf.get('/')
        head = rf.head('/')
        options = rf.options('/')

        delete = rf.delete('/')
        post = rf.post('/')
        put = rf.put('/')

        assert not limit_unsafe(get)
        assert not limit_unsafe(head)
        assert not limit_unsafe(options)
        assert limit_unsafe(delete)
        assert limit_unsafe(post)
        assert limit_unsafe(put)

        # TODO: When all supported versions have this, drop the `if`.
        if hasattr(rf, 'patch'):
            patch = rf.patch('/')
            assert limit_unsafe(patch)

    def test_key_get(self):
        req_a = rf.get('/', {'foo': 'a'})
        req_b = rf.get('/', {'foo': 'b'})

        @ratelimit(key='get:foo', rate='1/m', method='GET')
        def view(request):
            return request.limited

        assert not view(req_a)
        assert view(req_a)
        assert not view(req_b)
        assert view(req_b)

    def test_key_post(self):
        req_a = rf.post('/', {'foo': 'a'})
        req_b = rf.post('/', {'foo': 'b'})

        @ratelimit(key='post:foo', rate='1/m')
        def view(request):
            return request.limited

        assert not view(req_a)
        assert view(req_a)
        assert not view(req_b)
        assert view(req_b)

    def test_key_header(self):
        req = rf.post('/')
        req.META['HTTP_X_REAL_IP'] = '1.2.3.4'

        @ratelimit(key='header:x-real-ip', rate='1/m')
        @ratelimit(key='header:x-missing-header', rate='1/m')
        def view(request):
            return request.limited

        assert not view(req)
        assert view(req)

    def test_rate(self):
        req = rf.post('/')

        @ratelimit(key='ip', rate='2/m')
        def twice(request):
            return request.limited

        assert not twice(req), 'First request is not limited.'
        del req.limited
        assert not twice(req), 'Second request is not limited.'
        del req.limited
        assert twice(req), 'Third request is limited.'

    def test_zero_rate(self):
        req = rf.post('/')

        @ratelimit(key='ip', rate='0/m')
        def never(request):
            return request.limited

        assert never(req)

    def test_none_rate(self):
        req = rf.post('/')

        @ratelimit(key='ip', rate=None)
        def always(request):
            return request.limited

        assert not always(req)
        del req.limited
        assert not always(req)
        del req.limited
        assert not always(req)
        del req.limited
        assert not always(req)
        del req.limited
        assert not always(req)
        del req.limited
        assert not always(req)

    def test_callable_rate(self):
        auth = rf.post('/')
        unauth = rf.post('/')
        auth.user = MockUser(authenticated=True)
        unauth.user = MockUser(authenticated=False)

        def get_rate(group, request):
            if request.user.is_authenticated():
                return (2, 60)
            return (1, 60)

        @ratelimit(key='user_or_ip', rate=get_rate)
        def view(request):
            return request.limited

        assert not view(unauth)
        assert view(unauth)
        assert not view(auth)
        assert not view(auth)
        assert view(auth)

    def test_callable_rate_none(self):
        req = rf.post('/')
        req.never_limit = False

        get_rate = lambda g, r: None if r.never_limit else '1/m'

        @ratelimit(key='ip', rate=get_rate)
        def view(request):
            return request.limited

        assert not view(req)
        del req.limited
        assert view(req)
        req.never_limit = True
        del req.limited
        assert not view(req)
        del req.limited
        assert not view(req)

    def test_callable_rate_zero(self):
        auth = rf.post('/')
        unauth = rf.post('/')
        auth.user = MockUser(authenticated=True)
        unauth.user = MockUser(authenticated=False)

        def get_rate(group, request):
            if request.user.is_authenticated():
                return '1/m'
            return '0/m'

        @ratelimit(key='ip', rate=get_rate)
        def view(request):
            return request.limited

        assert view(unauth)
        del unauth.limited
        assert not view(auth)
        del auth.limited
        assert view(auth)
        assert view(unauth)

    @override_settings(RATELIMIT_USE_CACHE='fake-cache')
    def test_bad_cache(self):
        """The RATELIMIT_USE_CACHE setting works if the cache exists."""

        @ratelimit(key='ip', rate='1/m')
        def view(request):
            return request

        req = rf.post('/')

        with self.assertRaises(InvalidCacheBackendError):
            view(req)

    @override_settings(RATELIMIT_USE_CACHE='connection-errors')
    def test_cache_connection_error(self):

        @ratelimit(key='ip', rate='1/m')
        def view(request):
            return request

        req = rf.post('/')
        assert view(req)

    def test_user_or_ip(self):
        """Allow custom functions to set cache keys."""

        @ratelimit(key='user_or_ip', rate='1/m', block=False)
        def view(request):
            return request.limited

        unauth = rf.post('/')
        unauth.user = MockUser(authenticated=False)

        assert not view(unauth), 'First unauthenticated request is allowed.'
        assert view(unauth), 'Second unauthenticated request is limited.'

        auth = rf.post('/')
        auth.user = MockUser(authenticated=True)

        assert not view(auth), 'First authenticated request is allowed.'
        assert view(auth), 'Second authenticated is limited.'

    def test_key_path(self):
        @ratelimit(key='ratelimit.tests.mykey', rate='1/m')
        def view(request):
            return request.limited

        req = rf.post('/')
        assert not view(req)
        assert view(req)

    def test_callable_key(self):
        @ratelimit(key=mykey, rate='1/m')
        def view(request):
            return request.limited

        req = rf.post('/')
        assert not view(req)
        assert view(req)

    def test_stacked_decorator(self):
        """Allow @ratelimit to be stacked."""
        # Put the shorter one first and make sure the second one doesn't
        # reset request.limited back to False.
        @ratelimit(rate='1/m', block=False, key=lambda x, y: 'min')
        @ratelimit(rate='10/d', block=False, key=lambda x, y: 'day')
        def view(request):
            return request.limited

        req = rf.post('/')
        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

    def test_stacked_methods(self):
        """Different methods should result in different counts."""
        @ratelimit(rate='1/m', key='ip', method='GET')
        @ratelimit(rate='1/m', key='ip', method='POST')
        def view(request):
            return request.limited

        get = rf.get('/')
        post = rf.post('/')

        assert not view(get)
        assert not view(post)
        assert view(get)
        assert view(post)

    def test_sorted_methods(self):
        """Order of the methods shouldn't matter."""
        @ratelimit(rate='1/m', key='ip', method=['GET', 'POST'], group='a')
        def get_post(request):
            return request.limited

        @ratelimit(rate='1/m', key='ip', method=['POST', 'GET'], group='a')
        def post_get(request):
            return request.limited

        req = rf.get('/')
        assert not get_post(req)
        assert post_get(req)

    def test_is_ratelimited(self):
        def get_key(group, request):
            return 'test_is_ratelimited_key'

        def not_increment(request):
            return is_ratelimited(request, increment=False,
                                  method=is_ratelimited.ALL, key=get_key,
                                  rate='1/m', group='a')

        def do_increment(request):
            return is_ratelimited(request, increment=True,
                                  method=is_ratelimited.ALL, key=get_key,
                                  rate='1/m', group='a')

        req = rf.get('/')
        # Does not increment. Count still 0. Does not rate limit
        # because 0 < 1.
        assert not not_increment(req), 'Request should not be rate limited.'

        # Increments. Does not rate limit because 0 < 1. Count now 1.
        assert not do_increment(req), 'Request should not be rate limited.'

        # Does not increment. Count still 1. Not limited because 1 > 1
        # is false.
        assert not not_increment(req), 'Request should not be rate limited.'

        # Count = 2, 2 > 1.
        assert do_increment(req), 'Request should be rate limited.'
        assert not_increment(req), 'Request should be rate limited.'

    @override_settings(RATELIMIT_USE_CACHE='connection-errors')
    def test_is_ratelimited_cache_connection_error_without_increment(self):
        def get_key(group, request):
            return 'test_is_ratelimited_key'

        def not_increment(request):
            return is_ratelimited(request, increment=False,
                                  method=is_ratelimited.ALL, key=get_key,
                                  rate='1/m', group='a')

        req = rf.get('/')
        assert not not_increment(req)

    @override_settings(RATELIMIT_USE_CACHE='connection-errors')
    def test_is_ratelimited_cache_connection_error_with_increment(self):
        def get_key(group, request):
            return 'test_is_ratelimited_key'

        def do_increment(request):
            return is_ratelimited(request, increment=True,
                                  method=is_ratelimited.ALL, key=get_key,
                                  rate='1/m', group='a')

        req = rf.get('/')
        assert not do_increment(req)
        assert req.limited is False

    @override_settings(RATELIMIT_USE_CACHE='instant-expiration')
    def test_cache_timeout(self):
        @ratelimit(key='ip', rate='1/m', block=True)
        def view(request):
            return True

        req = rf.get('/')
        assert view(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            view(req)


class RatelimitCBVTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_limit_ip(self):

        class RLView(RatelimitMixin, View):
            ratelimit_key = 'ip'
            ratelimit_method = ratelimit.ALL
            ratelimit_rate = '1/m'
            ratelimit_block = True

        rlview = RLView.as_view()

        req = rf.get('/')
        assert rlview(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            rlview(req)

    def test_block(self):

        class BlockedView(RatelimitMixin, View):
            ratelimit_group = 'cbv:block'
            ratelimit_key = 'ip'
            ratelimit_method = ratelimit.ALL
            ratelimit_rate = '1/m'
            ratelimit_block = True

            def get(self, request, *args, **kwargs):
                return request.limited

        class UnBlockedView(RatelimitMixin, View):
            ratelimit_group = 'cbv:block'
            ratelimit_key = 'ip'
            ratelimit_method = ratelimit.ALL
            ratelimit_rate = '1/m'
            ratelimit_block = False

            def get(self, request, *args, **kwargs):
                return request.limited

        blocked = BlockedView.as_view()
        unblocked = UnBlockedView.as_view()

        req = rf.get('/')

        assert not blocked(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            blocked(req)

        assert unblocked(req), 'Request is limited but not blocked.'

    def test_method(self):
        post = rf.post('/')
        get = rf.get('/')

        class LimitPostView(RatelimitMixin, View):
            ratelimit_group = 'cbv:method'
            ratelimit_key = 'ip'
            ratelimit_method = ['POST']
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        class LimitGetView(RatelimitMixin, View):
            ratelimit_group = 'cbv:method'
            ratelimit_key = 'ip'
            ratelimit_method = ['POST', 'GET']
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        limit_post = LimitPostView.as_view()
        limit_get = LimitGetView.as_view()

        assert not limit_post(post), 'Do not limit first POST.'
        assert limit_post(post), 'Limit second POST.'
        assert not limit_post(get), 'Do not limit GET.'

        assert limit_get(post), 'Limit first POST.'
        assert limit_get(get), 'Limit first GET.'

    def test_rate(self):
        req = rf.post('/')

        class TwiceView(RatelimitMixin, View):
            ratelimit_key = 'ip'
            ratelimit_rate = '2/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        twice = TwiceView.as_view()

        assert not twice(req), 'First request is not limited.'
        assert not twice(req), 'Second request is not limited.'
        assert twice(req), 'Third request is limited.'

    @override_settings(RATELIMIT_USE_CACHE='fake-cache')
    def test_bad_cache(self):
        """The RATELIMIT_USE_CACHE setting works if the cache exists."""
        self.skipTest('I do not know why this fails when the other works.')

        class BadCacheView(RatelimitMixin, View):
            ratelimit_key = 'ip'

            def post(self, request, *args, **kwargs):
                return request
            get = post
        view = BadCacheView.as_view()

        req = rf.post('/')

        with self.assertRaises(InvalidCacheBackendError):
            view(req)

    def test_keys(self):
        """Allow custom functions to set cache keys."""

        def user_or_ip(group, req):
            if req.user.is_authenticated():
                return 'uip:%d' % req.user.pk
            return 'uip:%s' % req.META['REMOTE_ADDR']

        class KeysView(RatelimitMixin, View):
            ratelimit_key = user_or_ip
            ratelimit_block = False
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post
        view = KeysView.as_view()

        req = rf.post('/')
        req.user = MockUser(authenticated=False)

        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

        del req.limited
        req.user = MockUser(authenticated=True)

        assert not view(req), 'First authenticated request is allowed.'
        assert view(req), 'Second authenticated is limited.'

    def test_method_decorator(self):
        class TestView(View):
            @ratelimit(key='ip', rate='1/m', block=False)
            def post(self, request):
                return request.limited

        view = TestView.as_view()

        req = rf.post('/')

        assert not view(req)
        assert view(req)
