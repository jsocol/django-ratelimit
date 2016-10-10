VERSION = (1, 0, 1)
__version__ = '.'.join(map(str, VERSION))

ALL = (None,)  # Sentinel value for all HTTP methods.
UNSAFE = ['DELETE', 'PATCH', 'POST', 'PUT']
