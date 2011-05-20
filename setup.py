from setuptools import setup, find_packages

from ratelimit import VERSION

setup(
    name='django-ratelimit',
    version='.'.join(map(str, VERSION)),
    description='Cache-based rate-limiting for Django.',
    long_description=open('README.rst').read(),
    author='James Socol',
    author_email='james@mozilla.com',
    url='http://github.com/jsocol/django-ratelimit',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    package_data = { '': ['README.rst'] },
    install_requires=['django'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: Web Environment :: Mozilla',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
