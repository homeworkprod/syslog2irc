"""
syslog2irc.signals
~~~~~~~~~~~~~~~~~~

Signals

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from blinker import signal


syslog_message_received = signal('syslog-message-received')
irc_channel_joined = signal('irc-channel-joined')
message_received = signal('message-received')
message_approved = signal('message-approved')
