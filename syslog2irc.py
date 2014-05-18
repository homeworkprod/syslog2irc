#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Requirements
------------

- Python 2.7+ (tested with 2.7.6) or 3.2+ (tested with 3.2.3, 3.3.5,
  and 3.4.0)
- irc_ (tested with 8.9.1)
- blinker_ (tested with 1.3)
- enum34_ (tested with 1.0) on Python versions before 3.4


Installation
------------

irc_ and blinker_ can be installed via pip_:

.. code:: sh

    $ pip install irc blinker

As of Python 3.4, an enum module is part of the standard library. For
older versions of Python, install the enum34_ module:

.. code:: sh

    $ pip install enum34


Configuration
-------------

Setup your ``syslog.conf`` or ``rsyslog.conf`` (commonly found in
``/etc``) to send syslog messages to syslog2IRC on the default syslog
port (514, UDP, as assigned by IANA_)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

Or, when syslog2IRC listens on a non-default port (here: 11514)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on:11514

To specify which IRC channels to join and forward syslog messages to,
create ``IrcChannel`` instances and reference them in the ``routes``
mapping.

A simple routing from the default syslog port, 514, to a single IRC
channel without a password looks like this:

.. code:: python

    irc_channel1 = IrcChannel('#examplechannel1')

    routes = {
        514: [irc_channel1],
    }

In a more complex setup, syslog messages could be received on two ports
(514 and 55514), with those received on the first port being forwarded
to two IRC channels, and those received on the letter port being
forwarded exclusively to the second channel.

.. code:: python

    irc_channel1 = IrcChannel('#examplechannel1')
    irc_channel2 = IrcChannel('#examplechannel2', password='zePassword')

    routes = {
          514: [irc_channel1, irc_channel2],
        55514: [irc_channel2],
    }


Usage
-----

You might want to familiarize yourself with the available command line
options first:

.. code:: sh

    $ python syslog2irc.py -h

If no options are given, the IRC component will not be used. Instead,
syslog messages will be written to STDOUT. This is helpful during setup
of syslog message reception. Abort execution by pressing <Control-C>.

.. code:: sh

    $ python syslog2irc.py

Send some messages to syslog2IRC using your system's syslog message
sender tool (`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

Note that each message will appear twice on the console syslog2IRC was
started because the handler itself will write it there anyway (so you
have a log on what would be sent to IRC).

If receiving syslog messages works, connect to an IRC server:

.. code:: sh

    $ python syslog2irc.py --irc-server irc.example.com

After a moment, you should see that syslog2IRC has connected to the
server. The IRC bot should then enter the channel(s) you have configured
(see Configuration_).

To use another port on the IRC server than the default (6667), specify
it like this (6669 in this case):

.. code:: sh

    $ python syslog2irc.py --irc-server irc.example.com:6669

In order to shut down syslog2IRC, send a query message with the text
"shutdown!" to the IRC bot. It should then quit, and syslog2IRC should
exit.


Further Reading
---------------

For more information, see `RFC 3164`_, "The BSD syslog Protocol".

Please note that there is `RFC 5424`_, "The Syslog Protocol", which
obsoletes `RFC 3164`_. syslog2IRC, however, only implements the latter.


.. _irc:      https://bitbucket.org/jaraco/irc
.. _blinker:  http://pythonhosted.org/blinker/
.. _enum34:   https://pypi.python.org/pypi/enum34
.. _pip:      http://www.pip-installer.org/
.. _IANA:     http://www.iana.org/
.. _RFC 3164: http://tools.ietf.org/html/rfc3164
.. _RFC 5424: http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2014 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 15-May-2014 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
:Version: 0.6
"""

from __future__ import print_function
import argparse
from collections import defaultdict, namedtuple
from datetime import datetime
from enum import Enum, unique
from itertools import chain, islice, takewhile
try:
    # Python 2.x
    from SocketServer import BaseRequestHandler, ThreadingUDPServer
except ImportError:
    # Python 3.x
    from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys
from threading import Thread
from time import sleep

from blinker import signal
from irc.bot import ServerSpec, SingleServerIRCBot


DEFAULT_IRC_PORT = ServerSpec('').port


# A note on threads (implementation detail):
#
# This tool uses threads. Besides the main thread, there are two
# additional threads: one for the syslog message receiver and one for
# the IRC bot. Both are configured to be daemon threads.
#
# A Python application exits if no more non-daemon threads are running.
#
# In order to exit syslog2IRC when shutdown is requested on IRC, the IRC
# bot will call `die()`, which will join the IRC bot thread. The main
# thread and the (daemonized) syslog message receiver thread remain.
#
# Additionally, a dedicated signal is sent that sets a flag that causes
# the main loop to stop. As the syslog message receiver thread is the
# only one left, but runs as a daemon, the application exits.
#
# The STDOUT announcer, on the other hand, does not run in a thread. The
# user has to manually interrupt the application to exit.
#
# For details, see the documentation on the `threading` module that is
# part of Python's standard library.


# -------------------------------------------------------------------- #
# signals


syslog_message_received = signal('syslog-message-received')
irc_channel_joined = signal('irc-channel-joined')
shutdown_requested = signal('shutdown-requested')


# -------------------------------------------------------------------- #
# syslog


@unique
class SyslogFacility(Enum):
    kernel = 0
    user = 1
    mail = 2
    system_daemons = 3
    security4 = 4
    internal = 5
    line_printer = 6
    network_news = 7
    uucp = 8
    clock9 = 9
    security10 = 10
    ftp = 11
    ntp = 12
    log_audit = 13
    log_alert = 14
    clock15 = 15
    local0 = 16
    local1 = 17
    local2 = 18
    local3 = 19
    local4 = 20
    local5 = 21
    local6 = 22
    local7 = 23

    @property
    def description(self):
        return SYSLOG_FACILITY_DESCRIPTIONS[self.value]


SYSLOG_FACILITY_DESCRIPTIONS = {
    0: 'kernel messages',
    1: 'user-level messages',
    2: 'mail system',
    3: 'system daemons',
    4: 'security/authorization messages',
    5: 'messages generated internally by syslogd',
    6: 'line printer subsystem',
    7: 'network news subsystem',
    8: 'UUCP subsystem',
    9: 'clock daemon',
    10: 'security/authorization messages',
    11: 'FTP daemon',
    12: 'NTP subsystem',
    13: 'log audit',
    14: 'log alert',
    15: 'clock daemon',
    16: 'local use 0 (local0)',
    17: 'local use 1 (local1)',
    18: 'local use 2 (local2)',
    19: 'local use 3 (local3)',
    20: 'local use 4 (local4)',
    21: 'local use 5 (local5)',
    22: 'local use 6 (local6)',
    23: 'local use 7 (local7)',
}


@unique
class SyslogSeverity(Enum):
    emergency = 0
    alert = 1
    critical = 2
    error = 3
    warning = 4
    notice = 5
    informational = 6
    debug = 7


SyslogMessage = namedtuple('SyslogMessage',
    'facility severity timestamp hostname message')


class SyslogMessageParser(object):
    """Parse syslog messages."""

    @classmethod
    def parse(cls, data):
        parser = cls(data)

        facility_id, severity_id = parser._parse_priority_value()
        facility = SyslogFacility(facility_id)
        severity = SyslogSeverity(severity_id)
        timestamp = parser._parse_timestamp()
        hostname = parser._parse_hostname()
        message = ''.join(parser.data_iter)

        return SyslogMessage(facility, severity, timestamp, hostname,
            message)

    def __init__(self, data):
        max_bytes = 1024  # as stated by the RFC
        self.data_iter = iter(data[:max_bytes])

    def _parse_priority_value(self):
        """Parse the priority value to extract facility and severity
        IDs.
        """
        start_delim = self._take_slice(1)
        assert start_delim == '<'

        priority_value = self._take_until('>')
        assert len(priority_value) in {1, 2, 3}

        facility_id, severity_id = divmod(int(priority_value), 8)
        return facility_id, severity_id

    def _parse_timestamp(self):
        """Parse timestamp into a `datetime` instance."""
        timestamp_str = self._take_slice(15)
        nothing = self._take_until(' ')  # Advance to next part.
        assert nothing == ''

        timestamp = datetime.strptime(timestamp_str, '%b %d %H:%M:%S')
        timestamp = timestamp.replace(year=datetime.today().year)
        return timestamp

    def _parse_hostname(self):
        return self._take_until(' ')

    def _take_until(self, value):
        return ''.join(takewhile(lambda c: c != value, self.data_iter))

    def _take_slice(self, n):
        return ''.join(islice(self.data_iter, n))


def format_syslog_message(message):
    """Format a syslog message to be displayed."""
    def _generate():
        if message.timestamp is not None:
            timestamp_format = '%Y-%m-%d %H:%M:%S'
            formatted_timestamp = message.timestamp.strftime(
                timestamp_format)
            yield '[{}] '.format(formatted_timestamp)

        if message.hostname is not None:
            yield '({}) '.format(message.hostname)

        yield '[{0.severity.name}]: {0.message}'.format(message)

    return ''.join(_generate())


class SyslogRequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            data = self.request[0].strip().decode('ascii')
            message = SyslogMessageParser.parse(data)
        except ValueError:
            print('Invalid message received from {}:{:d}.'.format(
                *self.client_address))
            return

        port = self.server.get_port()
        syslog_message_received.send(port,
            source_address=self.client_address, message=message)


class SyslogReceiveServer(ThreadingUDPServer):
    """UDP server that waits for syslog messages."""

    def __init__(self, port):
        ThreadingUDPServer.__init__(self, ('', port),
            SyslogRequestHandler)

    @classmethod
    def start(cls, port):
        """Start in a separate thread."""
        try:
            receiver = cls(port)
        except Exception as e:
            sys.stderr.write('Error {0.errno:d}: {0.strerror}\n'
                .format(e))
            sys.stderr.write(
                'Probably no permission to open port {}. '
                'Try to specify a port number above 1,024 (or even '
                '4,096) and up to 65,535.\n'.format(port))
            sys.exit(1)

        thread_name = 'SyslogReceiveServer-port{:d}'.format(port)
        start_thread(receiver.serve_forever, thread_name)

    def get_port(self):
        return self.server_address[1]


def start_syslog_message_receivers(ports):
    """Start one syslog message receiving server for each port."""
    for port in ports:
        SyslogReceiveServer.start(port)


# -------------------------------------------------------------------- #
# IRC


class IrcChannel(namedtuple('IrcChannel', 'name password')):
    """An IRC channel with optional password."""

    def __new__(cls, name, password=None):
        return super(IrcChannel, cls).__new__(cls, name, password)


class IrcBot(SingleServerIRCBot):
    """An IRC bot to forward syslog messages to IRC channels."""

    def __init__(self, server_spec, nickname, realname, channels):
        print('Connecting to IRC server {0.host}:{0.port:d} ...'
            .format(server_spec))
        SingleServerIRCBot.__init__(self, [server_spec], nickname,
            realname)
        # Note: `self.channels` already exists in super class.
        self.channels_to_join = channels

    def get_version(self):
        return 'syslog2IRC'

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        print('Connected to {}:{:d}.'
            .format(*conn.socket.getsockname()))

        channel_names = sorted(c.name for c in self.channels_to_join)
        print('Joining channels: {}'.format(', '.join(channel_names)))

        for channel in self.channels_to_join:
            conn.join(channel.name, channel.password or '')

    def on_nicknameinuse(self, conn, event):
        """Choose another nickname if conflicting."""
        self._nickname += '_'
        conn.nick(self._nickname)

    def on_join(self, conn, event):
        """Successfully joined channel."""
        joined_nick = event.source.nick
        channel = event.target

        if joined_nick == self._nickname:
            print('Joined IRC channel {}.'.format(channel))
            irc_channel_joined.send(channel=channel)

    def on_badchannelkey(self, conn, event):
        """Channel could not be joined due to wrong password."""
        channel = event.arguments[0]
        print('Cannot join channel {} (bad key).'.format(channel))

    def on_privmsg(self, conn, event):
        """React on private messages.

        Shut down, for example.
        """
        whonick = event.source.nick
        message = event.arguments[0]
        if message == 'shutdown!':
            print('Shutdown requested on IRC by user {}.'
                .format(whonick))
            shutdown_requested.send()
            self.die('Shutting down.')  # Joins IRC bot thread.

    def say(self, channel, message):
        """Say message on channel."""
        self.connection.privmsg(channel, message)


# -------------------------------------------------------------------- #
# announcing


class IrcAnnouncer(object):
    """Announce syslog messages on IRC."""

    def __init__(self, server, nickname, realname, channels):
        self.bot = IrcBot(server, nickname, realname, channels)
        start_thread(self.bot.start, 'IrcAnnouncer')

    def announce(self, channel, message):
        self.bot.say(channel, message)


class StdoutAnnouncer(object):
    """Announce syslog messages on STDOUT."""

    def announce(self, channel, message):
        print('{}> {}'.format(channel, message))


def start_announcer(args, irc_channels):
    """Create and return an announcer according to the configuration."""
    if not args.irc_server:
        print('No IRC server specified; will write to STDOUT instead.')
        return StdoutAnnouncer()

    return IrcAnnouncer(args.irc_server, args.irc_nickname,
        args.irc_realname, irc_channels)


# -------------------------------------------------------------------- #
# threads


def start_thread(target, name):
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name)
    t.daemon = True
    t.start()


# -------------------------------------------------------------------- #


class Processor(object):

    def __init__(self, announcer):
        self.announcer = announcer

        self.ports_to_channel_names = defaultdict(set)

        self.ready = True

        self.shutdown = False
        shutdown_requested.connect(self.handle_shutdown_requested)

    def register_route(self, port, channel_name):
        self.ports_to_channel_names[port].add(channel_name)

    def wait_for_signal_before_starting(self, signal):
        """Don't accept messages until the signal is sent."""
        self.ready = False
        signal.connect(self.handle_start_signal)

    def handle_start_signal(self, sender, **kw):
        self.ready = True

    def handle_shutdown_requested(self, sender):
        self.shutdown = True

    def run(self):
        """Run the main loop until shutdown is requested."""
        while not self.ready:
            sleep(0.5)

        print('Starting to accept syslog messages.')
        syslog_message_received.connect(
            self.handle_syslog_message_received)

        while not self.shutdown:
            sleep(0.5)

        print('Shutting down ...')

    def handle_syslog_message_received(self, port, source_address=None,
            message=None):
        """Log and announce an incoming syslog message."""
        source = '{0[0]}:{0[1]:d}'.format(source_address)

        print('Received message from {} on port {:d} -> {}'
            .format(source, port, message))

        formatted_message = format_syslog_message(message)
        irc_message = '{} {}'.format(source, formatted_message)
        for channel_name in self.ports_to_channel_names[port]:
            self.announcer.announce(channel_name, irc_message)


# -------------------------------------------------------------------- #
# command line argument parsing


def parse_args():
    """Setup and apply the command line arguments parser."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--irc-nickname',
        dest='irc_nickname',
        default='syslog',
        help='the IRC nickname the bot should use',
        metavar='NICKNAME')

    parser.add_argument('--irc-realname',
        dest='irc_realname',
        default='syslog2IRC',
        help='the IRC realname the bot should use',
        metavar='REALNAME')

    parser.add_argument('--irc-server',
        dest='irc_server',
        type=parse_irc_server_arg,
        help='IRC server (host and, optionally, port) to connect to'
            + ' [e.g. "irc.example.com" or "irc.example.com:6669";'
            + ' default port: {:d}]'.format(DEFAULT_IRC_PORT),
        metavar='SERVER')

    return parser.parse_args()

def parse_irc_server_arg(value):
    """Parse a hostname with optional port."""
    fragments = value.split(':', 1)
    if len(fragments) > 1:
        fragments[1] = int(fragments[1])
    return ServerSpec(*fragments)


# -------------------------------------------------------------------- #

def map_channel_names_to_ports(routes):
    channel_names_to_ports = defaultdict(set)
    for port, channels in routes.items():
        for channel in channels:
            channel_names_to_ports[channel.name].add(port)
    return channel_names_to_ports

def start_processor(announcer, channel_names_to_ports, use_irc):
    processor = Processor(announcer)

    @irc_channel_joined.connect
    def register_route(sender, channel=None):
        ports = channel_names_to_ports[channel]
        for port in ports:
            processor.register_route(port, channel)

    if use_irc:
        processor.wait_for_signal_before_starting(irc_channel_joined)
    else:
        for channel in channel_names_to_ports.keys():
            irc_channel_joined.send(channel=channel)

    processor.run()

def main(routes):
    """Application entry point"""
    args = parse_args()

    irc_channels = frozenset(chain(*routes.values()))
    announcer = start_announcer(args, irc_channels)

    ports = routes.keys()
    start_syslog_message_receivers(ports)

    channel_names_to_ports = map_channel_names_to_ports(routes)
    use_irc = bool(args.irc_server)
    start_processor(announcer, channel_names_to_ports, use_irc)

if __name__ == '__main__':
    # IRC channels to join
    irc_channel1 = IrcChannel('#examplechannel1')
    irc_channel2 = IrcChannel('#examplechannel2', password='zePassword')

    # routing for syslog messages from the ports on which they are
    # received to the IRC channels they should be announced on
    routes = {
          514: [irc_channel1, irc_channel2],
        55514: [irc_channel2],
    }

    main(routes)
