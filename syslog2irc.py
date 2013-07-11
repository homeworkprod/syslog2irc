#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Installation
------------

Needs Python 2.7+ or Python 3+ (tested with 3.3.2).

Also requires the `python-irclib`_ package (tested with 8.3.1), which can be
installed via pip_:

.. code:: sh

    $ pip install irc


Configuration
-------------

Setup your ``syslog.conf`` or ``rsyslog.conf`` (commonly found in ``/etc``) to
send syslog messages to syslog2IRC on the default syslog port (514, UDP, as
assigned by IANA_)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

Or, when syslog2IRC listens on a non-default port (here: 11514)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on:11514

To specify the IRC channels to join, adjust the list ``IRC_CHANNELS``, which
is expected to contain (channel name, password) pairs.


Usage
-----

You might want to familiarze yourself with the available command line options
first:

.. code:: sh

    $ python syslog2irc.py -h

If no options are given, the IRC component will not be used. Instead, syslog
messages will be written to STDOUT. This is helpful during setup of syslog
message reception. Abort execution by pressing <Control-C>.

.. code:: sh

    $ python syslog2irc.py

If the syslog deamon is configured to forward to a port other than the
default, specify that:

.. code:: sh

    $ python syslog2irc.py --syslog-port 11514

Send some messages to syslog2IRC using your system's syslog message sender tool
(`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

Note that each message will appear twice on the console syslog2IRC was started
because the handler itself will write it there anyway (so you have a log on
what would be sent to IRC).

If receiving syslog messages works, connect to an IRC server:

.. code:: sh

    $ python syslog2irc.py irc.example.com

After a moment, you should see that syslog2IRC has connected to the server.
The IRC bot should then enter the channel(s) you have configured (see
Configuration_).

To use another port on the IRC server than the default (6667), specify it like
this (6669 in this case):

.. code:: sh

    $ python syslog2irc.py irc.example.com:6669

In order to shut down syslog2IRC, send a query message with the text
"shutdown!" to the IRC bot. It should then quit, and syslog2IRC should exit.


Further Reading
---------------

For more information, see `RFC 3164`_, "The BSD syslog Protocol".

Please note that there is `RFC 5424`_, "The Syslog Protocol", which obsoletes
`RFC 3164`_. syslog2IRC, however, only implements the latter.


.. _python-irclib:  http://python-irclib.sourceforge.net/
.. _pip:            http://www.pip-installer.org/
.. _IANA:           http://www.iana.org/
.. _RFC 3164:       http://tools.ietf.org/html/rfc3164
.. _RFC 5424:       http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2013 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 09-Jul-2013 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
"""

from __future__ import print_function
import argparse
from collections import namedtuple
from datetime import datetime
from itertools import islice, takewhile
try:
    # Python 2.x
    from Queue import Empty, Queue
except ImportError:
    # Python 3.x
    from queue import Empty, Queue
try:
    # Python 2.x
    from SocketServer import BaseRequestHandler, ThreadingUDPServer
except ImportError:
    # Python 3.x
    from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys
import threading
from threading import Thread
from time import sleep

from irc.bot import SingleServerIRCBot


DEFAULT_IRC_PORT = 6667
DEFAULT_SYSLOG_PORT = 514


# A note on threads (implementation detail):
#
# This tool uses threads. Besides the main thread, there are two additional
# threads: one for the syslog message receiver and one for the IRC bot. Both
# are configured to be daemon threads.
#
# A Python application exits if no more non-daemon threads are running.
#
# In order to exit syslog2IRC when shutdown is requested on IRC, the IRC bot
# will call `die()` which joins the IRC bot thread. The main thread and the
# (daemonized) syslog message receiver thread remain.
#
# The queue-processing loop regularly queries the announcer if it is still
# "alive" (i.e. if the IRC bot thread is still running). If it is not, the
# queue processor (which runs in the main thread) calls `sys.exit()`. As the
# syslog message receiver thread is the only one left, but runs as a daemon,
# the application exits.
#
# The STDOUT announcer, on the other hand, does not run in a thread. The user
# has to manually interrupt the application to exit.
#
# For details, see the documentation on the `threading` module that is part of
# Python's standard library.


# ---------------------------------------------------------------- #
# syslog stuff


class SyslogMessageParser(object):
    """Parse syslog messages."""

    @classmethod
    def parse(cls, data):
        parser = cls(data)

        facility_id, severity_id = parser._parse_priority_value()
        timestamp = parser._parse_timestamp()
        hostname = parser._parse_hostname()
        message = ''.join(parser.data_iter)

        return SyslogMessage(facility_id, severity_id, timestamp, hostname, message)

    def __init__(self, data):
        self.data_iter = iter(data[:1024])  # 1024 bytes max (as stated by the RFC).

    def _parse_priority_value(self):
        """Parse the priority value to extract facility and severity IDs."""
        start_delim = self._take_slice(1)
        assert start_delim == '<'
        priority_value = self._take_until('>')
        assert len(priority_value) in [1, 2, 3]
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


class SyslogMessage(namedtuple('SyslogMessage',
        'facility_id severity_id timestamp hostname message'
    )):
    """A syslog message."""

    FACILITIES = {
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

    SEVERITIES = {
        0: 'Emergency',
        1: 'Alert',
        2: 'Critical',
        3: 'Error',
        4: 'Warning',
        5: 'Notice',
        6: 'Informational',
        7: 'Debug',
        }

    @property
    def facility_name(self):
        return SyslogMessage.FACILITIES[self.facility_id]

    @property
    def severity_name(self):
        return SyslogMessage.SEVERITIES[self.severity_id]


def format_syslog_message(syslog_message):
    """Format a syslog message to be displayed."""
    def _generate():
        timestamp_format = '%Y-%m-%d %H:%M:%S'
        if syslog_message.timestamp is not None:
            yield '[%s] ' % syslog_message.timestamp.strftime(timestamp_format)

        if syslog_message.hostname is not None:
            yield '(%s) ' % syslog_message.hostname

        yield '[%s]: %s' % (syslog_message.severity_name,
            syslog_message.message)

    return ''.join(_generate())


class SyslogRequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            data = self.request[0].strip()
            data = data.decode('ascii')
            syslog_message = SyslogMessageParser.parse(data)
        except ValueError:
            print('Invalid message received from %s:%d.' % self.client_address)
        else:
            self.server.queue.put((self.client_address, syslog_message))
            print('%s:%d ->' % self.client_address, syslog_message)


class SyslogReceiveServer(ThreadingUDPServer):
    """UDP server that waits for syslog messages."""

    def __init__(self, port):
        ThreadingUDPServer.__init__(self, ('', port), SyslogRequestHandler)
        self.queue = Queue()


# ---------------------------------------------------------------- #
# IRC bot stuff


class IrcBot(SingleServerIRCBot):
    """An IRC bot to forward syslog messages to the configured channels."""

    def __init__(self, host_and_port, nickname, realname, channels):
        print('Connecting to IRC server %s:%d ...' % host_and_port)
        SingleServerIRCBot.__init__(self, [host_and_port], nickname, realname)
        self.channels_with_keys = channels

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        print('Connected to %s:%d.' % conn.socket.getsockname())
        for channel, key in self.channels_with_keys:
            conn.join(channel, key)

    def on_nicknameinuse(self, conn, event):
        """Choose another nickname if conflicting."""
        self._nickname += '_'
        conn.nick(self._nickname)

    def on_ctcp(self, conn, event):
        """Answer CTCP PING and VERSION queries."""
        whonick = event.source.nick
        message = event.arguments[0].lower()
        if message == 'version':
            conn.notice(whonick, 'syslog2IRC')
        elif message == 'ping':
            conn.pong(whonick)

    def on_privmsg(self, conn, event):
        """React on private messages.

        Shut down, for example.
        """
        whonick = event.source.nick
        message = event.arguments[0]
        if message == 'shutdown!':
            print('Shutdown requested on IRC by user %s.' % whonick)
            self.die('Shutting down.')  # Joins IRC bot thread.

    def say(self, msg):
        """Say message to channels."""
        for channel, key in self.channels_with_keys:
            self.connection.privmsg(channel, msg)


# ---------------------------------------------------------------- #


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
            + ' default port: %d]' % DEFAULT_IRC_PORT,
        metavar='SERVER')

    parser.add_argument('--syslog-port',
        dest='syslog_port',
        type=int,
        default=DEFAULT_SYSLOG_PORT,
        help='the port to listen on for syslog messages [default: %d]'
            % DEFAULT_SYSLOG_PORT,
        metavar='PORT')

    return parser.parse_args()

_HostAndPort = namedtuple('HostAndPort', ['host', 'port'])

def HostAndPort(host, port=DEFAULT_IRC_PORT):
    return _HostAndPort(host, int(port))

def parse_irc_server_arg(value):
    """Parse a hostname with optional port."""
    fragments = value.split(':', 1)
    return HostAndPort(*fragments)

def start_thread(target, name):
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name)
    t.daemon = True
    t.start()


class IrcAnnouncer(object):
    """Announce syslog messages on IRC."""

    THREAD_NAME = 'IrcBot'

    def __init__(self, server, nickname, realname, channels):
        self.bot = IrcBot(server, nickname, realname, channels)
        start_thread(self.bot.start, self.THREAD_NAME)

    def announce(self, message):
        self.bot.say(message)

    def is_alive(self):
        return is_thread_alive(self.THREAD_NAME)


class StdoutAnnouncer(object):
    """Announce syslog messages on STDOUT."""

    def announce(self, message):
        print(message)

    def is_alive(self):
        return True


def start_announcer(args, irc_channels):
    """Create and return an announcer according to the configuration."""
    if args.irc_server:
        return IrcAnnouncer(args.irc_server, args.irc_nickname,
            args.irc_realname, irc_channels)
    else:
        print('No IRC server specified; will write to STDOUT instead.')
        return StdoutAnnouncer()

def start_syslog_message_receiver(port):
    """Prepare the server to receive syslog messages on the given port and
    start it in a separate thread.

    Return the receiver queue.
    """
    try:
        receiver = SyslogReceiveServer(port)
    except PermissionError:
        sys.stderr.write('No permission to open port %d. Try to specify a '
            'port number above 1,024 (or even 4,096) and up to 65,535 using '
            'the `--syslog-port` option.\n' % port)
        sys.exit(1)
    start_thread(receiver.serve_forever, 'SyslogReceiveServer')
    return receiver.queue

def process_queue(announcer, queue, delay=2):
    """Process received messages in queue."""
    while True:
        sleep(delay)

        if not announcer.is_alive():
            print('Exiting ...')
            sys.exit(0)

        try:
            sender_address, syslog_message = queue.get_nowait()
        except Empty:
            continue

        output = ('%s:%d ' % sender_address) \
            + format_syslog_message(syslog_message)
        announcer.announce(output)

def is_thread_alive(name):
    """Return true if a thread with the given name is alive."""
    alive_threads = threading.enumerate()
    return any(filter(lambda t: t.name == name, alive_threads))

def main(irc_channels):
    args = parse_args()
    announcer = start_announcer(args, irc_channels)
    queue = start_syslog_message_receiver(args.syslog_port)
    process_queue(announcer, queue)

if __name__ == '__main__':
    # Configure IRC channels to join.
    IRC_CHANNELS = [
        ('#examplechannel', 'secret'),
    ]

    main(IRC_CHANNELS)
