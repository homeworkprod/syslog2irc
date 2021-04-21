"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from pathlib import Path

import pytest

from syslog2irc.cli import parse_args


def test_parse_args_without_args():
    with pytest.raises(SystemExit):
        actual = parse_args([])


def test_parse_args_with_config_filename_arg():
    actual = parse_args(['config.toml'])

    assert actual.config_filename == Path('config.toml')
