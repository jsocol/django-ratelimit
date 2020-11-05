SECRET_KEY = "ratelimit"

INSTALLED_APPS = ("ratelimit",)

RATELIMIT_USE_CACHE = "default"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ratelimit-tests",
    },
    "connection-errors": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "test-connection-errors",
    },
    "connection-errors-redis": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://test-connection-errors",
        "OPTIONS": {
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "instant-expiration": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "test-instant-expiration",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "test.db",
    },
}


INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.admin",
    "ratelimit",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
