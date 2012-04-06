#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.

Requires the `python-irclib`_ package.

Setup your ``syslog.conf``::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

For more information, see `RFC 3164`, "The BSD syslog Protocol".

:Copyright: 2007-2012 Jochen Kupperschmidt
:Date: 06-Apr-2012 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.

.. _python-irclib:  http://python-irclib.sourceforge.net/
.. _RFC 3164:       http://tools.ietf.org/html/rfc3164
"""

import argparse
from collections import namedtuple
from Queue import Queue
from SocketServer import BaseRequestHandler, ThreadingUDPServer
from threading import Thread
from time import sleep, strftime, strptime

from ircbot import SingleServerIRCBot
from irclib import nm_to_n


DEFAULT_IRC_PORT = 6667
DEFAULT_SYSLOG_PORT = 514


# ---------------------------------------------------------------- #
# syslog stuff

class SyslogMessage(object):
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

    def __init__(self, data):
        # 1024 bytes max says RFC.
        self.payload = data[:1024]
        self.parse_priority()
        self.parse_header()

    def parse_priority(self):
        """Extract and resolve priority."""
        prio, self.payload = self.payload.split('>', 1)
        self.priority_id = int(prio[1:])
        self.facility_id, self.severity_id = divmod(self.priority_id, 8)
        self.facility = self.FACILITIES[self.facility_id]
        self.severity = self.SEVERITIES[self.severity_id]

    def parse_header(self):
        """Try to extract a RFC-compliant TIMESTAMP/HOSTNAME header."""
        try:
            self.timestamp = strptime(self.payload[:15], '%b %d %H:%M:%S')
        except ValueError:
            # Header is not RFC-compliant.
            self.timestamp, self.hostname = None, None
        else:
            self.hostname, self.payload = self.payload[16:].split(' ', 1)

    def __str__(self):
        s = ''
        if self.timestamp is not None:
            s += '[%s] ' % strftime('%Y-%m-%d %H:%M:%S', self.timestamp)
        if self.hostname is not None:
            s += '(%s) ' % self.hostname
        s += '[%s]: %s' % (self.severity, self.payload)
        return s


class SyslogRequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            msg = SyslogMessage(self.request[0].strip())
        except ValueError:
            msg = 'Invalid message.'
        else:
            self.server.queue.put((self.client_address, msg))
        print ('%s:%d' % self.client_address), str(msg)


class SyslogReceiveServer(ThreadingUDPServer):
    """UDP server that waits for syslog messages."""

    def __init__(self, port):
        ThreadingUDPServer.__init__(self, ('', port), SyslogRequestHandler)
        self.queue = Queue()


# ---------------------------------------------------------------- #
# IRC bot stuff

class SyslogBot(SingleServerIRCBot):

    def __init__(self, hostAndPort, channel_list, nickname='Syslog',
            realname='syslog'):
        print 'Connecting to IRC server %s:%d ...' % hostAndPort
        SingleServerIRCBot.__init__(self, [hostAndPort], nickname, realname)
        self.channel_list = channel_list

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        print 'Connected to %s:%d.' % conn.socket.getsockname()
        for channel, key in self.channel_list:
            conn.join(channel, key)

    def on_nicknameinuse(self, conn, event):
        """Choose another nickname if conflicting."""
        self._nickname += '_'
        conn.nick(self._nickname)

    def on_ctcp(self, conn, event):
        """Answer CTCP PING and VERSION queries."""
        whonick = nm_to_n(event.source())
        message = event.arguments()[0].lower()
        if message == 'version':
            conn.notice(whonick, 'Syslog2IRC')
        elif message == 'ping':
            conn.pong(whonick)

    def on_privmsg(self, conn, event):
        """React on private messages.

        Die, for example.
        """
        whonick = nm_to_n(event.source())
        message = event.arguments()[0]
        if message == 'die!':
            print 'Shutting down as requested by %s...' % whonick
            self.die('Shutting down.')

    def say(self, msg):
        """Say message to channels."""
        for channel, key in self.channel_list:
            self.connection.privmsg(channel, msg)


# ---------------------------------------------------------------- #

def process_queue(announce_callback, queue, delay=2):
    """Process received messages in queue."""
    while True:
        sleep(delay)
        try:
            addr, msg = queue.get()
        except Empty:
            continue
        announce_callback('%s:%d ' % addr + str(msg))

def parse_args():
    """Parse command line arguments."""

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

if __name__ == '__main__':
    args = parse_args()

    # Set IRC connection parameters.
    irc_channels = [('#examplechannel', 'secret')]

    if args.irc_enabled:
        # Prepare and start IRC bot.
        bot = SyslogBot(args.irc_server, irc_channels)
        Thread(target=bot.start).start()
        announce = bot.say
    else:
        # Just display messages on STDOUT.
        print 'IRC output is disabled.'
        def announce(s):
            print s

    # Prepare and start syslog message receiver.
    receiver = SyslogReceiveServer(args.syslog_port)
    Thread(target=receiver.serve_forever).start()

    process_queue(announce, receiver.queue)
