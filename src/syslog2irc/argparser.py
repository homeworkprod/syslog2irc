"""
syslog2irc.argparser
~~~~~~~~~~~~~~~~~~~~

Command line argument parsing

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from argparse import ArgumentParser
import dataclasses

from .irc import IrcServer


DEFAULT_IRC_PORT = IrcServer('').port


def parse_args(args=None):
    """Parse command line arguments."""
    parser = create_arg_parser()
    parsed = parser.parse_args(args)

    irc_server = parsed.irc_server
    if irc_server is not None:
        parsed.irc_server = dataclasses.replace(
            irc_server, ssl=parsed.irc_server_ssl
        )

    return parsed


def create_arg_parser():
    """Prepare the command line arguments parser."""
    parser = ArgumentParser()

    parser.add_argument(
        '--irc-nickname',
        dest='irc_nickname',
        default='syslog',
        help='the IRC nickname the bot should use',
        metavar='NICKNAME',
    )

    parser.add_argument(
        '--irc-realname',
        dest='irc_realname',
        default='syslog2IRC',
        help='the IRC realname the bot should use',
        metavar='REALNAME',
    )

    parser.add_argument(
        '--irc-server',
        dest='irc_server',
        type=parse_irc_server_arg,
        help='IRC server (host and, optionally, port) to connect to'
        + ' [e.g. "irc.example.com" or "irc.example.com:6669";'
        + ' default port: {:d}]'.format(DEFAULT_IRC_PORT),
        metavar='SERVER',
    )

    parser.add_argument(
        '--irc-server-ssl',
        dest='irc_server_ssl',
        action='store_true',
        help='use SSL to connect to the IRC server',
    )

    return parser


def parse_irc_server_arg(value):
    """Parse a hostname with optional port."""
    fragments = value.split(':', 1)
    if len(fragments) > 1:
        fragments[1] = int(fragments[1])
    return IrcServer(*fragments)
