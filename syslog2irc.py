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

Start syslog2IRC and tell it what IRC server to connect to:

.. code:: sh

    $ python syslog2irc.py irc.example.com

After a moment, you should see that syslog2IRC has connected to the server.
The IRC bot should then enter the channel(s) you have configured (see
Configuration_).

To use another port than the default (6667), specify it like this (6669 in
this case):

.. code:: sh

    $ python syslog2irc.py irc.example.com:6669

If you configured the syslog daemon to send messages to another port, specify
that:

.. code:: sh

    $ python syslog2irc.py --syslog-port 11514 irc.example.com

To test functionality in a limited scope, first have syslog2IRC print syslog
messages to STDOUT instead of IRC by supplied the `--irc-disabled` option (you
still have to specify an IRC server, though it will be ignored):

.. code:: sh

    $ python syslog2irc.py --irc-disabled irc.example.com

Note that a message will appear twice on STDOUT because it is written there
already by the handler itself (so you have a log on what would be sent to
IRC).

Then send some messages to it using your system's syslog message sender tool
(`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

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
:Date: 08-Jul-2013 (original release: 12-Apr-2007)
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
        return self.FACILITIES[self.facility_id]

    @property
    def severity_name(self):
        return self.SEVERITIES[self.severity_id]

    def __str__(self):
        s = ''
        if self.timestamp is not None:
            s += '[%s] ' % self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        if self.hostname is not None:
            s += '(%s) ' % self.hostname
        s += '[%s]: %s' % (self.severity_name, self.message)
        return s


class SyslogRequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            data = self.request[0].strip()
            data = data.decode('ascii')
            msg = SyslogMessageParser.parse(data)
        except ValueError:
            msg = 'Invalid message.'
        else:
            self.server.queue.put((self.client_address, msg))
        print('%s:%d' % self.client_address, msg)


class SyslogReceiveServer(ThreadingUDPServer):
    """UDP server that waits for syslog messages."""

    def __init__(self, port):
        ThreadingUDPServer.__init__(self, ('', port), SyslogRequestHandler)
        self.queue = Queue()


# ---------------------------------------------------------------- #
# IRC bot stuff


class IrcBot(SingleServerIRCBot):
    """An IRC bot to forward syslog messages to the configured channels."""

    def __init__(self, host_and_port, channel_list, nickname, realname):
        print('Connecting to IRC server %s:%d ...' % host_and_port)
        SingleServerIRCBot.__init__(self, [host_and_port], nickname, realname)
        self.channel_list = channel_list

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        print('Connected to %s:%d.' % conn.socket.getsockname())
        for channel, key in self.channel_list:
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
            print('Shutting down as requested on IRC by user %s ...' % whonick)
            self.die('Shutting down.')  # Joins IRC bot thread.

    def say(self, msg):
        """Say message to channels."""
        for channel, key in self.channel_list:
            self.connection.privmsg(channel, msg)


# ---------------------------------------------------------------- #


def parse_args():
    """Setup and apply the command line arguments parser."""

    HostAndPort = namedtuple('HostAndPort', ['host', 'port'])

    def host_and_port(port_default):
        def parse_host_and_port(value):
            """Parse a hostname with optional port."""
            host, port_str = value.partition(':')[::2]
            port = int(port_str) if port_str else port_default
            return HostAndPort(host, port)
        return parse_host_and_port

    parser = argparse.ArgumentParser()

    parser.add_argument('--irc-disabled',
        dest='irc_enabled',
        action='store_false',
        default=True,
        help='display messages on STDOUT instead of forwarding them to IRC')

    parser.add_argument('--irc-nickname',
        dest='irc_nickname',
        default='syslog',
        help='the IRC nickname the bot should use')

    parser.add_argument('--irc-realname',
        dest='irc_realname',
        default='syslog2IRC',
        help='the IRC realname the bot should use')

    parser.add_argument('--syslog-port',
        dest='syslog_port',
        type=int,
        default=DEFAULT_SYSLOG_PORT,
        metavar='PORT',
        help='the port to listen on for syslog messages [default: %d]'
            % DEFAULT_SYSLOG_PORT)

    parser.add_argument('irc_server',
        type=host_and_port(DEFAULT_IRC_PORT),
        help='IRC server (host and, optionally, port) to connect to'
            + ' [e.g. "irc.example.com" or "irc.example.com:6669";'
            + ' default port: %d]' % DEFAULT_IRC_PORT,
        metavar='<IRC server>')

    return parser.parse_args()

def start_thread(target, name):
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name)
    t.daemon = True
    t.start()

def start_announcer(args, irc_channels):
    """If IRC output is enabled, configure the IRC bot and start it in a
    separate thread. If it is disabled, just write to STDOUT.

    Return the announce callback.
    """
    if args.irc_enabled:
        # Prepare and start IRC bot.
        bot = IrcBot(args.irc_server, irc_channels, args.irc_nickname,
            args.irc_realname)
        start_thread(bot.start, 'IrcBot')
        return bot.say
    else:
        # Just display messages on STDOUT.
        print('IRC output is disabled; writing to STDOUT instead.')
        return print

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

def process_queue(announce_callback, queue, delay=2):
    """Process received messages in queue."""
    while True:
        sleep(delay)

        if not is_thread_alive('IrcBot'):
            print('IRC bot thread is no longer alive; exiting.')
            sys.exit(0)

        try:
            addr, msg = queue.get_nowait()
        except Empty:
            continue

        announce_callback('%s:%d ' % addr + str(msg))

def is_thread_alive(name):
    """Return true if a thread with the given name is alive."""
    alive_threads = threading.enumerate()
    return any(filter(lambda t: t.name == name, alive_threads))

def main(irc_channels):
    args = parse_args()
    announce_callback = start_announcer(args, irc_channels)
    queue = start_syslog_message_receiver(args.syslog_port)
    process_queue(announce_callback, queue)

if __name__ == '__main__':
    # Configure IRC channels to join.
    IRC_CHANNELS = [
        ('#examplechannel', 'secret'),
    ]

    main(IRC_CHANNELS)
