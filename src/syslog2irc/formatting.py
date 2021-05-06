"""
syslog2irc.formatting
~~~~~~~~~~~~~~~~~~~~~

Message formatting

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from typing import Tuple

from syslogmp import Message as SyslogMessage


MESSAGE_TEXT_ENCODING = 'utf-8'


def format_message(
    source_address: Tuple[str, int], message: SyslogMessage
) -> str:
    """Format syslog message to be displayed on IRC."""
    source_host = source_address[0]
    source_port = source_address[1]

    timestamp_format = '%Y-%m-%d %H:%M:%S'
    formatted_timestamp = message.timestamp.strftime(timestamp_format)

    severity_name = message.severity.name

    # Important: The message text is a byte string.
    text = message.message.decode(MESSAGE_TEXT_ENCODING)

    # Remove leading and trailing newlines. Those would result in
    # additional lines on IRC with the usual metadata but with an
    # empty message text.
    text = text.strip('\n')

    return (
        f'{source_host}:{source_port:d} '
        f'[{formatted_timestamp}] '
        f'({message.hostname}) '
        f'[{severity_name}]: {text}'
    )
