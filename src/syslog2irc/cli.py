"""
syslog2irc.cli
~~~~~~~~~~~~~~

Command line argument parsing

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from argparse import ArgumentParser, Namespace
import dataclasses
from typing import List, Optional

from . import VERSION
from .irc import IrcServer


DEFAULT_IRC_PORT = IrcServer('').port


def parse_args(args: Optional[List[str]] = None) -> Namespace:
    """Parse command line arguments."""
    parser = create_arg_parser()
    parsed = parser.parse_args(args)

    irc_server = parsed.irc_server
    if irc_server is not None:
        parsed.irc_server = dataclasses.replace(
            irc_server, ssl=parsed.irc_server_ssl
        )

    return parsed


def create_arg_parser() -> ArgumentParser:
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
        + f' default port: {DEFAULT_IRC_PORT:d}]',
        metavar='SERVER',
    )

    parser.add_argument(
        '--irc-server-ssl',
        dest='irc_server_ssl',
        action='store_true',
        help='use SSL to connect to the IRC server',
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'syslog2IRC {VERSION}',
    )

    return parser


def parse_irc_server_arg(value: str) -> IrcServer:
    """Parse a hostname with optional port."""
    fragments = value.split(':', 1)
    host = fragments[0]
    if len(fragments) > 1:
        port = int(fragments[1])
        return IrcServer(host, port)
    else:
        return IrcServer(host)
