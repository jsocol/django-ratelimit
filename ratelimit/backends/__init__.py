import hashlib

__all__ = ['RateLimitBackend']


class RateLimitBackend(object):
    """ Base class for all rate limit backends """

    def _get_keys(self, request, ip=True, field=None, keyfuncs=None):
        keys = []
        if ip:
            keys.append('ip:' + request.META['REMOTE_ADDR'])
        if field is not None:
            if not isinstance(field, (list, tuple)):
                field = [field]
            for f in field:
                val = getattr(request, request.method).get(f, '').encode('utf-8')
                val = hashlib.sha1(val).hexdigest()
                keys.append(u'field:%s:%s' % (f, val))
        if keyfuncs:
            if not isinstance(keyfuncs, (list, tuple)):
                keyfuncs = [keyfuncs]
            for k in keyfuncs:
                keys.append(k(request))
        return keys

    def hit(self, request, ip, field, keys, period):
        """ Records a hit and returns the current coutns """
        raise NotImplemented
