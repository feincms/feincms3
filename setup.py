#!/usr/bin/env python

from io import open
import os
from setuptools import setup, find_packages


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding='utf-8') as handle:
        return handle.read()


setup(
    name='feincms3',
    version=__import__('feincms3').__version__,
    description='feincms3',
    long_description=read('README.rst'),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='https://github.com/matthiask/feincms3/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=find_packages(
        exclude=['tests', 'testapp']
    ),
    include_package_data=True,
    # install_requires=[
    #     'Django',
    #     'django-ckeditor',
    #     'django-content-editor',
    #     'django-cte-forest',
    #     'django-versatileimagefield',
    #     'feincms-cleanse',
    #     'requests',
    # ],
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    zip_safe=False,
)
