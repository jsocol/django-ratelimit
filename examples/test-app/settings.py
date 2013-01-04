SECRET_KEY = 'ratelimit'

INSTALLED_APPS = (
    'django_nose',
    'ratelimit',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-tests',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}

TEST_RUNNER = 'django_nose.runner.NoseTestSuiteRunner'
