"""
syslog2irc.cli
~~~~~~~~~~~~~~

Command line argument parsing

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Optional

from . import VERSION


def parse_args(args: Optional[List[str]] = None) -> Namespace:
    """Parse command line arguments."""
    parser = _create_arg_parser()
    return parser.parse_args(args)


def _create_arg_parser() -> ArgumentParser:
    """Prepare the command line arguments parser."""
    parser = ArgumentParser()

    parser.add_argument(
        '--version',
        action='version',
        version=f'syslog2IRC {VERSION}',
    )

    parser.add_argument(
        'config_filename',
        type=Path,
    )

    return parser
