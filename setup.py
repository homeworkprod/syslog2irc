import codecs
import sys

from setuptools import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='syslog2IRC',
    version='0.9.2-dev',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Internet',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: System :: Systems Administration',
    ],
    packages=['syslog2irc'],
    install_requires=[
        'blinker==1.4',
        'irc >= 8.9.1',
        'syslogmp==0.3',
    ],
)
