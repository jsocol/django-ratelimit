try:
    from django.core.cache import caches

    def get_cache(name):
        return caches[name]
except ImportError:  # Django <1.7
    from django.core.cache import get_cache
