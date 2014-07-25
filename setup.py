#!/usr/bin/env python
try:
    from setuptools import setup 
except ImportError, err:
    from distutils.core import setup
    
from djax import VERSION

setup(
    name='Djax',
    version='.'.join(map(str,VERSION)),
    description='Integrates Django projects with Axilent.',
    packages=['djax','djax.management.commands','pax'],
    license='BSD',
    author='Loren Davie',
    author_email='code@axilent.com',
    url='http://github.com/Axilent/Djax',
    install_requires=['sharrock-client','Django','python-dateutil'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)