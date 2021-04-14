"""
:Copyright: 2007-2021 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.argparser import parse_args


@pytest.mark.parametrize(
    'arg_value, expected',
    [
        ([                              ], 'syslog'    ),
        (['--irc-nickname', 'AwesomeBot'], 'AwesomeBot'),
    ],
)
def test_irc_nickname(arg_value, expected):
    actual = parse_args(arg_value)
    assert actual.irc_nickname == expected


@pytest.mark.parametrize(
    'arg_value, expected',
    [
        ([                                      ], 'syslog2IRC'        ),
        (['--irc-realname', 'awesomest bot ever'], 'awesomest bot ever'),
    ],
)
def test_irc_realname(arg_value, expected):
    actual = parse_args(arg_value)
    assert actual.irc_realname == expected


@pytest.mark.parametrize(
    'arg_value, expected_host, expected_port',
    [
        (['--irc-server', 'localhost'     ], 'localhost', 6667),
        (['--irc-server', '127.0.0.1'     ], '127.0.0.1', 6667),
        (['--irc-server', '127.0.0.1:6669'], '127.0.0.1', 6669),
    ],
)
def test_parse_irc_server(arg_value, expected_host, expected_port):
    actual = parse_args(arg_value)
    assert actual.irc_server.host == expected_host
    assert actual.irc_server.port == expected_port


@pytest.mark.parametrize(
    'arg_value, expected',
    [
        ([                  ], False),
        (['--irc-server-ssl'], True ),
    ],
)
def test_irc_server_ssl_option(arg_value, expected):
    actual = parse_args(arg_value)
    assert actual.irc_server_ssl == expected
