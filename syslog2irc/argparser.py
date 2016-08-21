# -*- coding: utf-8 -*-

"""
syslog2irc.argparser
~~~~~~~~~~~~~~~~~~~~

Command line argument parsing

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from __future__ import absolute_import
from argparse import ArgumentParser

from irc.bot import ServerSpec


DEFAULT_IRC_PORT = ServerSpec('').port


def parse_args(args=None):
    """Parse command line arguments."""
    parser = create_arg_parser()
    return parser.parse_args(args)


def create_arg_parser():
    """Prepare the command line arguments parser."""
    parser = ArgumentParser()

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
        help='IRC server (host and, optionally, port and password)'
            + ' to connect to'
            + ' [e.g. "irc.example.com", "irc.example.com:6669"'
            + ' or "irc.example.com:6669:password;"'
            + ' default port: {:d}]'.format(DEFAULT_IRC_PORT),
        metavar='SERVER')

    parser.add_argument('--irc-server-ssl',
        dest='irc_server_ssl',
        action='store_true',
        help='use SSL to connect to the IRC server')

    return parser


def parse_irc_server_arg(value):
    """Parse a hostname with optional port."""
    fragments = value.split(':', 2)
    if len(fragments) > 1:
        fragments[1] = int(fragments[1])
    return ServerSpec(*fragments)
