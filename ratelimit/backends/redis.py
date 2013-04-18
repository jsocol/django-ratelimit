from __future__ import absolute_import
from ratelimit.backends import RateLimitBackend
from django.conf import settings
import redis as r
from ratelimit.exceptions import InvalidConfig

import logging
logger = logging.getLogger(__name__)

import time


class RedisRateLimitBackend(RateLimitBackend):
    def __init__(self):
        redis_config = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
        self._get_redis_client(redis_config)

    def _trim(self, keys, timeout, now):
        """
        Remove obsolete members of zset that are
        outside the ratelimit sliding window
        """
        for key in keys:
            logger.debug("Triming values from %s (%s, %s)" % (key, 0, now - 1 - timeout * 1000))
            self.redis_client.zremrangebyscore(key, 0, now - 1 - timeout * 1000)

    def _incr(self, keys, timeout=60):
        now = int(time.time() * 1000)
        logger.debug("NOW => %s" % now)
        # trim obsolete values from zrange
        self._trim(keys, timeout, now)
        counts = {}
        # add and count
        for key in keys:
            logger.debug("Setting %s => %s" % (key, now))
            self.redis_client.zadd(key, now, now)
            #extend expiration
            self.redis_client.expire(key, timeout)
            counts[key] = self.redis_client.zcount(key, now - timeout * 1000, now)
            logger.debug("counting values in %s between %s and %s: %s" % (key, now - timeout * 1000, now, counts[key]))
        return counts

    def _get_redis_client(self, configname):
        if configname not in settings.REDIS_SERVERS:
            logger.warning("Config %s not found" % configname)
            raise InvalidConfig

        hostname = settings.REDIS_SERVERS[configname]['HOST']
        port = 6379
        if 'PORT' in settings.REDIS_SERVERS[configname]:
            port = int(settings.REDIS_SERVERS[configname]['PORT'])

        timeout = 10
        if 'TIMEOUT' in settings.REDIS_SERVERS[configname]:
            timeout = settings.REDIS_SERVERS[configname]['TIMEOUT']
        logger.debug("Connecting to %s:%d (timeout: %s)" % (hostname, port, timeout))
        try:
            self.redis_client = r.client.StrictRedis(host=hostname, port=port, socket_timeout=timeout)
        except Exception as e:
            logger.debug(e)
            raise InvalidConfig
