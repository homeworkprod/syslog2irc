# -*- coding: utf-8 -*-

import codecs
import sys

from setuptools import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


# Require the 'enum34' package on Python versions before 3.4.
version_dependent_install_requires = []
if sys.version_info[:2] < (3, 4):
    version_dependent_install_requires.append('enum34')


setup(
    name='syslog2IRC',
    version='0.8',
    description='A proxy to forward syslog messages to IRC',
    long_description=long_description,
    url='http://homework.nwsnet.de/releases/c474/#syslog2irc',
    author='Jochen Kupperschmidt',
    author_email='homework@nwsnet.de',
    license='MIT',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Internet',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: System :: Systems Administration',
    ],
    install_requires=[
        'blinker >= 1.3',
        'irc >= 8.9.1',
        'syslogmp >= 0.1.1',
    ] + version_dependent_install_requires,
    tests_require=['nose2'],
    test_suite='nose2.collector.collector',
)
