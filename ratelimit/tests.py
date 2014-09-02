import django
from django.core.cache import cache, InvalidCacheBackendError
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.views.generic import View

from ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited
from ratelimit.mixins import RateLimitMixin
from ratelimit.utils import is_ratelimited, _split_rate


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

    def test_ip(self):
        @ratelimit(key='ip', method=None, rate='1/m', block=True)
        def view(request):
            return True

        req = RequestFactory().get('/')
        assert view(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            view(req)

    def test_block(self):
        @ratelimit(key='ip', method=None, rate='1/m', block=True)
        def blocked(request):
            return request.limited

        @ratelimit(key='ip', method=None, rate='1/m', block=False)
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

        @ratelimit(key='ip', rate='1/m', group='a')
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

    def test_key_get(self):
        req_a = RequestFactory().get('/', {'foo': 'a'})
        req_b = RequestFactory().get('/', {'foo': 'b'})

        @ratelimit(key='get:foo', rate='1/m', method='GET')
        def view(request):
            return request.limited

        assert not view(req_a)
        assert view(req_a)
        assert not view(req_b)
        assert view(req_b)

    def test_key_post(self):
        req_a = RequestFactory().post('/', {'foo': 'a'})
        req_b = RequestFactory().post('/', {'foo': 'b'})

        @ratelimit(key='post:foo', rate='1/m')
        def view(request):
            return request.limited

        assert not view(req_a)
        assert view(req_a)
        assert not view(req_b)
        assert view(req_b)

    def test_key_header(self):
        req = RequestFactory().post('/')
        req.META['HTTP_X_REAL_IP'] = '1.2.3.4'

        @ratelimit(key='header:x-real-ip', rate='1/m')
        def view(request):
            return request.limited

        assert not view(req)
        assert view(req)

    def test_key_field(self):
        james = RequestFactory().post('/', {'username': 'james'})
        john = RequestFactory().post('/', {'username': 'john'})

        @ratelimit(key='field:username', rate='1/m')
        def username(request):
            return request.limited

        assert not username(james), "james' first request is fine."
        assert username(james), "james' second request is limited."
        assert not username(john), "john's first request is fine."

    def test_field_unicode(self):
        post = RequestFactory().post('/', {'username': u'fran\xe7ois'})

        @ratelimit(key='field:username', rate='1/m')
        def view(request):
            return request.limited

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_field_empty(self):
        post = RequestFactory().post('/', {})

        @ratelimit(key='field:username', rate='1/m')
        def view(request):
            return request.limited

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_rate(self):
        req = RequestFactory().post('/')

        @ratelimit(key='ip', rate='2/m')
        def twice(request):
            return request.limited

        assert not twice(req), 'First request is not limited.'
        assert not twice(req), 'Second request is not limited.'
        assert twice(req), 'Third request is limited.'

    def test_callable_rate(self):
        auth = RequestFactory().post('/')
        unauth = RequestFactory().post('/')
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

    @override_settings(RATELIMIT_USE_CACHE='fake-cache')
    def test_bad_cache(self):
        """The RATELIMIT_USE_CACHE setting works if the cache exists."""

        @ratelimit(key='ip', rate='1/m')
        def view(request):
            return request

        req = RequestFactory().post('/')

        with self.assertRaises(InvalidCacheBackendError):
            view(req)

    def test_user_or_ip(self):
        """Allow custom functions to set cache keys."""

        @ratelimit(key='user_or_ip', rate='1/m', block=False)
        def view(request):
            return request.limited

        unauth = RequestFactory().post('/')
        unauth.user = MockUser(authenticated=False)

        assert not view(unauth), 'First unauthenticated request is allowed.'
        assert view(unauth), 'Second unauthenticated request is limited.'

        auth = RequestFactory().post('/')
        auth.user = MockUser(authenticated=True)

        assert not view(auth), 'First authenticated request is allowed.'
        assert view(auth), 'Second authenticated is limited.'

    def test_key_path(self):
        @ratelimit(key='ratelimit.tests.mykey', rate='1/m')
        def view(request):
            return request.limited

        req = RequestFactory().post('/')
        assert not view(req)
        assert view(req)

    def test_stacked_decorator(self):
        """Allow @ratelimit to be stacked."""
        # Put the shorter one first and make sure the second one doesn't
        # reset request.limited back to False.
        @ratelimit(rate='1/m', block=False, key=lambda x: 'min')
        @ratelimit(rate='10/d', block=False, key=lambda x: 'day')
        def view(request):
            return request.limited

        req = RequestFactory().post('/')
        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

    def test_stacked_methods(self):
        """Different methods should result in different counts."""
        @ratelimit(rate='1/m', key='ip', method='GET')
        @ratelimit(rate='1/m', key='ip', method='POST')
        def view(request):
            return request.limited

        get = RequestFactory().get('/')
        post = RequestFactory().post('/')

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

        req = RequestFactory().get('/')
        assert not get_post(req)
        assert post_get(req)

    def test_is_ratelimited(self):
        def get_key(request):
            return 'test_is_ratelimited_key'

        def not_increment(request):
            return is_ratelimited(request, increment=False, method=None,
                                  key=get_key, rate='1/m', group='a')

        def do_increment(request):
            return is_ratelimited(request, increment=True, method=None,
                                  key=get_key, rate='1/m', group='a')

        req = RequestFactory().get('/')
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


class RateLimitCBVTests(TestCase):

    def setUp(self):
        self.skipTest('no cbv yet')
        cache.clear()

    def test_limit_ip(self):

        class RLView(RateLimitMixin, View):
            ratelimit_ip = True
            ratelimit_method = None
            ratelimit_rate = '1/m'
            ratelimit_block = True

        rlview = RLView.as_view()

        req = RequestFactory().get('/')
        assert rlview(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            rlview(req)

    def test_block(self):

        class BlockedView(RateLimitMixin, View):
            ratelimit_ip = True
            ratelimit_method = None
            ratelimit_rate = '1/m'
            ratelimit_block = True

            def get(self, request, *args, **kwargs):
                return request.limited

        class UnBlockedView(RateLimitMixin, View):
            ratelimit_ip = True
            ratelimit_method = None
            ratelimit_rate = '1/m'
            ratelimit_block = False

            def get(self, request, *args, **kwargs):
                return request.limited

        blocked = BlockedView.as_view()
        unblocked = UnBlockedView.as_view()

        req = RequestFactory().get('/')

        assert not blocked(req), 'First request works.'
        with self.assertRaises(Ratelimited):
            blocked(req)

        assert unblocked(req), 'Request is limited but not blocked.'

    def test_method(self):
        rf = RequestFactory()
        post = rf.post('/')
        get = rf.get('/')

        class LimitPostView(RateLimitMixin, View):
            ratelimit_ip = True
            ratelimit_method = ['POST']
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        class LimitGetView(RateLimitMixin, View):
            ratelimit_ip = True
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

    def test_field(self):
        james = RequestFactory().post('/', {'username': 'james'})
        john = RequestFactory().post('/', {'username': 'john'})

        class UsernameView(RateLimitMixin, View):
            ratelimit_ip = False
            ratelimit_field = 'username'
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        username = UsernameView.as_view()
        assert not username(james), "james' first request is fine."
        assert username(james), "james' second request is limited."
        assert not username(john), "john's first request is fine."

    def test_field_unicode(self):
        post = RequestFactory().post('/', {'username': u'fran\xe7ois'})

        class UsernameView(RateLimitMixin, View):
            ratelimit_ip = False
            ratelimit_field = 'username'
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        view = UsernameView.as_view()

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_field_empty(self):
        post = RequestFactory().post('/', {})

        class EmptyFieldView(RateLimitMixin, View):
            ratelimit_ip = False
            ratelimit_field = 'username'
            ratelimit_rate = '1/m'

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post

        view = EmptyFieldView.as_view()

        assert not view(post), 'First request is not limited.'
        assert view(post), 'Second request is limited.'

    def test_rate(self):
        req = RequestFactory().post('/')

        class TwiceView(RateLimitMixin, View):
            ratelimit_ip = True
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

        class BadCacheView(RateLimitMixin, View):

            def post(self, request, *args, **kwargs):
                return request
            get = post
        view = BadCacheView.as_view()

        req = RequestFactory().post('/')

        with self.assertRaises(InvalidCacheBackendError):
            view(req)

    def test_keys(self):
        """Allow custom functions to set cache keys."""

        def user_or_ip(req):
            if req.user.is_authenticated():
                return 'uip:%d' % req.user.pk
            return 'uip:%s' % req.META['REMOTE_ADDR']

        class KeysView(RateLimitMixin, View):
            ratelimit_ip = False
            ratelimit_block = False
            ratelimit_rate = '1/m'
            ratelimit_keys = user_or_ip

            def post(self, request, *args, **kwargs):
                return request.limited
            get = post
        view = KeysView.as_view()

        req = RequestFactory().post('/')
        req.user = MockUser(authenticated=False)

        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

        del req.limited
        req.user = MockUser(authenticated=True)

        assert not view(req), 'First authenticated request is allowed.'
        assert view(req), 'Second authenticated is limited.'
