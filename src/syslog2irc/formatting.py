"""
syslog2irc.formatting
~~~~~~~~~~~~~~~~~~~~~

Message formatting

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from typing import Iterator, Tuple

from syslogmp import Message as SyslogMessage


MESSAGE_TEXT_ENCODING = 'utf-8'


def format_message(
    source_address: Tuple[str, int], message: SyslogMessage
) -> str:
    """Format syslog message to be displayed on IRC."""

    def _generate() -> Iterator[str]:
        yield f'{source_address[0]}:{source_address[1]:d} '

        timestamp_format = '%Y-%m-%d %H:%M:%S'
        formatted_timestamp = message.timestamp.strftime(timestamp_format)
        yield f'[{formatted_timestamp}] '

        yield f'({message.hostname}) '

        severity_name = message.severity.name

        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)

        # Remove leading and trailing newlines. Those would result in
        # additional lines on IRC with the usual metadata but with an
        # empty message text.
        message_text = message_text.strip('\n')

        yield f'[{severity_name}]: {message_text}'

    return ''.join(_generate())
