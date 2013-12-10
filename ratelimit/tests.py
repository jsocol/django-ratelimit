import django
from django.core.cache import cache, InvalidCacheBackendError
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.views.generic import View

from ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited
from ratelimit.mixins import RateLimitMixin
from ratelimit.helpers import is_ratelimited


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
        del req.limited
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

        del req.limited
        req.user = User(authenticated=True)

        assert not view(req), 'First authenticated request is allowed.'
        assert view(req), 'Second authenticated is limited.'

    def test_stacked_decorator(self):
        """Allow @ratelimit to be stacked."""
        # Put the shorter one first and make sure the second one doesn't
        # reset request.limited back to False.
        @ratelimit(ip=False, rate='1/m', block=False, keys=lambda x: 'min')
        @ratelimit(ip=False, rate='10/d', block=False, keys=lambda x: 'day')
        def view(request):
            return request.limited

        req = RequestFactory().post('/')
        assert not view(req), 'First unauthenticated request is allowed.'
        assert view(req), 'Second unauthenticated request is limited.'

    def test_is_ratelimited(self):
        def get_keys(request):
            return 'test_is_ratelimited_key'

        def not_increment(request):
            return is_ratelimited(request, increment=False, ip=False,
                                  method=None, keys=[get_keys], rate='1/m')

        def do_increment(request):
            return is_ratelimited(request, increment=True, ip=False,
                                  method=None, keys=[get_keys], rate='1/m')

        req = RequestFactory().get('/')
        # Does not increment. Count still 0. Does not rate limit
        # because 0 < 1.
        assert not not_increment(req), 'Request should not be rate limited.'

        # Increments. Does not rate limit because 0 < 1. Count now 1.
        assert not do_increment(req), 'Request should not be rate limited.'

        # Does not increment. Count still 1. Rate limits because 1 < 1
        # is false.
        assert not_increment(req), 'Request should be rate limited.'


#do it here, since python < 2.7 does not have unittest.skipIf
if django.VERSION >= (1, 4):
    class RateLimitCBVTests(TestCase):

        SKIP_REASON = u'Class Based View supported by Django >=1.4'

        def setUp(self):
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

        def test_skip_if(self):
            req = RequestFactory().post('/')

            class SkipIfView(RateLimitMixin, View):
                ratelimit_rate = '1/m'
                ratelimit_skip_if = lambda r: getattr(r, 'skip', False)

                def post(self, request, *args, **kwargs):
                    return request.limited
                get = post
            view = SkipIfView.as_view()

            assert not view(req), 'First request is not limited.'
            assert view(req), 'Second request is limited.'
            del req.limited
            req.skip = True
            assert not view(req), 'Skipped request is not limited.'

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
            req.user = User(authenticated=False)

            assert not view(req), 'First unauthenticated request is allowed.'
            assert view(req), 'Second unauthenticated request is limited.'

            del req.limited
            req.user = User(authenticated=True)

            assert not view(req), 'First authenticated request is allowed.'
            assert view(req), 'Second authenticated is limited.'
