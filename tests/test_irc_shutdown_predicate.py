# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from irc.bot import ServerSpec
from irc.client import Event, NickMask
from nose2.tools import params

from syslog2irc.irc import Bot
from syslog2irc.signals import shutdown_requested


class IrcShutdownPredicateTestCase(TestCase):

    @params(
        (None                                                         , 'anything' , False),
        (lambda nickmask, text: nickmask.nick == 'UserNick'           , 'anything' , True ),
        (lambda nickmask, text: nickmask.nick == 'OtherNick'          , 'anything' , False),
        (lambda nickmask, text: nickmask.host.endswith('.example.com'), 'anything' , True ),
        (lambda nickmask, text: nickmask.host.endswith('.example.net'), 'anything' , False),
        (lambda nickmask, text: text == 'shutdown!'                   , 'shutdown!', True ),
        (lambda nickmask, text: text == 'shutdown!'                   , 'something', False),
    )
    def test_shutdown_predicate(self, shutdown_predicate, text, expected):
        self.shutdown_signal_received = False

        bot = create_bot(shutdown_predicate)

        @shutdown_requested.connect
        def handle_shutdown_requested(sender):
            self.shutdown_signal_received = True

        send_privmsg(bot, text)

        self.assertEqual(self.shutdown_signal_received, expected)


def create_bot(shutdown_predicate):
    server = ServerSpec('irc.example.org')
    nickname = 'BotNick'
    realname = 'BotName'
    channels = []
    bot = Bot(server, nickname, realname, channels,
              shutdown_predicate=shutdown_predicate)

    # Prevent `SystemExit`.
    bot.die = lambda message: None

    return bot


def send_privmsg(bot, text):
    conn = None
    event = create_privmsg_event(text)
    bot.on_privmsg(conn, event)


def create_privmsg_event(text):
    source = NickMask('UserNick!user@machine23.example.com')
    target = 'BotNick'
    return Event('privmsg', source, target, [text])
