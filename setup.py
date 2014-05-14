#!/usr/env/bin python

from setuptools import setup


setup(
    name='syslog2IRC',
    version='0.5',
    description='A proxy to forward syslog messages to IRC',
    author='Jochen Kupperschmidt',
    author_email='homework@nwsnet.de',
    url='http://homework.nwsnet.de/releases/c474/#syslog2irc',
    install_requires=[
        'blinker >= 1.3',
        'irc >= 8.3.1',
        'enum34 >= 1.0',
    ],
)
