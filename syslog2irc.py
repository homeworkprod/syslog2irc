#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Requirements
------------

- Python 2.7+ or 3.3+
- irc_
- blinker_
- syslogmp_


Installation
------------

The required packages can be installed via pip_:

.. code:: sh

    $ pip install -r requirements.txt


Tests
-----

To run the tests:

.. code:: sh

    $ python setup.py test


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
.. _syslogmp: http://homework.nwsnet.de/releases/76d6/#syslogmp
.. _pip:      http://www.pip-installer.org/
.. _IANA:     http://www.iana.org/
.. _RFC 3164: http://tools.ietf.org/html/rfc3164
.. _RFC 5424: http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 10-Aug-2015 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
:Version: 0.8
"""

from __future__ import print_function
import argparse
from collections import defaultdict, namedtuple
from itertools import chain
try:
    # Python 2.x
    from SocketServer import BaseRequestHandler, ThreadingUDPServer
except ImportError:
    # Python 3.x
    from socketserver import BaseRequestHandler, ThreadingUDPServer
from ssl import wrap_socket as ssl_wrap_socket
import sys
from threading import Thread
from time import sleep

from blinker import signal
import irc
from irc.bot import ServerSpec, SingleServerIRCBot
import syslogmp


DEFAULT_IRC_PORT = ServerSpec('').port

MESSAGE_TEXT_ENCODING = 'utf-8'


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

        severity_name = message.severity.name
        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)
        yield '[{}]: {}'.format(severity_name, message_text)

    return ''.join(_generate())


class SyslogRequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            data = self.request[0]
            message = syslogmp.parse(data)
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

        thread_name = '{}-port{:d}'.format(cls.__name__, port)
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

    def __init__(self, server_spec, nickname, realname, channels, ssl=False):
        print('Connecting to IRC server {0.host}:{0.port:d} ...'
            .format(server_spec))

        connect_params = {}
        if ssl:
            ssl_factory = irc.connection.Factory(wrapper=ssl_wrap_socket)
            connect_params['connect_factory'] = ssl_factory

        SingleServerIRCBot.__init__(self, [server_spec], nickname,
            realname, **connect_params)

        # Note: `self.channels` already exists in super class.
        self.channels_to_join = channels

    def get_version(self):
        return 'syslog2IRC'

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        print('Connected to {}:{:d}.'
            .format(*conn.socket.getpeername()))

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

    def __init__(self, server, nickname, realname, channels, ssl=False):
        self.bot = IrcBot(server, nickname, realname, channels, ssl=ssl)

    def start(self):
        start_thread(self.bot.start, 'IrcAnnouncer')

    def announce(self, channel, message):
        self.bot.say(channel, message)


class StdoutAnnouncer(object):
    """Announce syslog messages on STDOUT."""

    def start(self):
        pass

    def announce(self, channel, message):
        print('{}> {}'.format(channel, message))


def create_announcer(args, irc_channels):
    """Create and return an announcer according to the configuration."""
    if not args.irc_server:
        print('No IRC server specified; will write to STDOUT instead.')
        return StdoutAnnouncer()

    return IrcAnnouncer(args.irc_server, args.irc_nickname,
        args.irc_realname, irc_channels, ssl=args.irc_server_ssl)


# -------------------------------------------------------------------- #
# threads


def start_thread(target, name):
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name)
    t.daemon = True
    t.start()


# -------------------------------------------------------------------- #


class Processor(object):

    def __init__(self, announcer, channel_names_to_ports):
        self.announcer = announcer
        self.channel_names_to_ports = channel_names_to_ports
        self.ports_to_channel_names = defaultdict(set)
        self.shutdown = False

    def connect_to_signals(self):
        irc_channel_joined.connect(self.enable_channel)
        shutdown_requested.connect(self.handle_shutdown_requested)
        syslog_message_received.connect(self.handle_syslog_message)

    def enable_channel(self, sender, channel=None):
        ports = self.channel_names_to_ports[channel]

        print('Enabled forwarding to channel {} from ports {}.'
            .format(channel, ports))

        for port in ports:
            self.ports_to_channel_names[port].add(channel)

    def handle_shutdown_requested(self, sender):
        self.shutdown = True

    def run(self):
        """Run the main loop until shutdown is requested."""
        while not self.shutdown:
            sleep(0.5)

        print('Shutting down ...')

    def handle_syslog_message(self, port, source_address=None,
            message=None):
        """Log and announce an incoming syslog message."""
        source = '{0[0]}:{0[1]:d}'.format(source_address)

        print('Received message from {} on port {:d} -> {}'
            .format(source, port, format_message_for_log(message)))

        formatted_message = format_syslog_message(message)
        irc_message = '{} {}'.format(source, formatted_message)
        for channel_name in self.ports_to_channel_names[port]:
            self.announcer.announce(channel_name, irc_message)


def format_message_for_log(message):
    facility_name = message.facility.name
    severity_name = message.severity.name
    timestamp_str = message.timestamp.isoformat()
    hostname = message.hostname

    return 'facility={}, severity={}, timestamp={}, hostname={}, message={}' \
           .format(facility_name, severity_name, timestamp_str, hostname,
                   message.message)


# -------------------------------------------------------------------- #
# command line argument parsing


def parse_args():
    """Parse command line arguments."""
    parser = create_arg_parser()
    return parser.parse_args()


def create_arg_parser():
    """Prepare the command line arguments parser."""
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

    parser.add_argument('--irc-server-ssl',
        dest='irc_server_ssl',
        action='store_true',
        help='use SSL to connect to the IRC server')

    return parser


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


def main(routes):
    """Application entry point"""
    args = parse_args()
    irc_channels = frozenset(chain(*routes.values()))
    channel_names_to_ports = map_channel_names_to_ports(routes)
    ports = routes.keys()

    announcer = create_announcer(args, irc_channels)
    processor = Processor(announcer, channel_names_to_ports)

    # Up to this point, no signals must have been sent.
    processor.connect_to_signals()

    # Signals are allowed be sent from here on.

    start_syslog_message_receivers(ports)
    announcer.start()

    if not args.irc_server:
        # Fake channel joins.
        for channel in channel_names_to_ports.keys():
            irc_channel_joined.send(channel=channel)

    processor.run()


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
