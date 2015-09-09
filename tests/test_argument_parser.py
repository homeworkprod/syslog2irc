# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from nose2.tools import params

from syslog2irc import create_arg_parser


class ArgumentParserTestCase(TestCase):

    @params(
        ([                              ], 'syslog'    ),
        (['--irc-nickname', 'AwesomeBot'], 'AwesomeBot'),
    )
    def test_irc_nickname(self, arg_value, expected):
        parser = create_arg_parser()
        actual = parser.parse_args(arg_value)
        self.assertEqual(actual.irc_nickname, expected)

    @params(
        ([                                      ], 'syslog2IRC'        ),
        (['--irc-realname', 'awesomest bot ever'], 'awesomest bot ever'),
    )
    def test_irc_realname(self, arg_value, expected):
        parser = create_arg_parser()
        actual = parser.parse_args(arg_value)
        self.assertEqual(actual.irc_realname, expected)

    @params(
        ([                  ], False),
        (['--irc-server-ssl'], True ),
    )
    def test_irc_server_ssl_option(self, arg_value, expected):
        parser = create_arg_parser()
        actual = parser.parse_args(arg_value)
        self.assertEqual(actual.irc_server_ssl, expected)

    @params(
        (['--irc-server', 'localhost'     ], 'localhost', 6667),
        (['--irc-server', '127.0.0.1'     ], '127.0.0.1', 6667),
        (['--irc-server', '127.0.0.1:6669'], '127.0.0.1', 6669),
    )
    def test_parse_irc_server(self, arg_value, expected_host, expected_port):
        parser = create_arg_parser()
        actual = parser.parse_args(arg_value)
        self.assertEqual(actual.irc_server.host, expected_host)
        self.assertEqual(actual.irc_server.port, expected_port)
