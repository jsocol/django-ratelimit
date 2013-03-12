def ip_only(request):
    """Get a key representing the IP address of a request."""
    return [u'ip:' + request.META['REMOTE_ADDR']]


def user_or_ip(request):
    """If the user is logged in, the key is the user name. If not,
    return the IP address."""
    if hasattr(request, 'user') and request.user.is_authenticated():
        return [u'user:' + request.user.username]
    else:
        return [u'ip:' + request.META['REMOTE_ADDR']]


def field(field):
    """Return a function that gets a field from a request's request
    variables (POST or GET).

    Use this like
 
        @ratelimit(keys=field('MOBILE'), ...)
        def foo(request):
            pass
    """

    if not isinstance(field, (list, tuple)):
        field = [field]

    def getter(request):
        keys = []
        for f in field:
            val = getattr(request, request.method).get(f, '')
            # Convert the string to only ascii.
            val = val.encode('utf-8')
            keys.append('field:%s:%s' % (f, val))
        return keys

    return getter
