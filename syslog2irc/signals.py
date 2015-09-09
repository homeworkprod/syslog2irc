# -*- coding: utf-8 -*-

"""
syslog2irc.signals
~~~~~~~~~~~~~~~~~~

Signals

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from blinker import signal


syslog_message_received = signal('syslog-message-received')
irc_channel_joined = signal('irc-channel-joined')
message_approved = signal('message-approved')
shutdown_requested = signal('shutdown-requested')
