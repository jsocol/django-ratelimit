
def my_ip(req):
    return req.META['MY_THING']

def callable_rate(group, request):
    if request.user.is_authenticated:
        return None
    return (0, 1)

def mykey(group, request):
    return request.META['REMOTE_ADDR'][::-1]

class CustomRatelimitedException(Exception):
    pass