"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from io import StringIO

from syslog2irc.config import load_config
from syslog2irc.irc import IrcChannel, IrcConfig, IrcServer
from syslog2irc.router import Route


TOML_CONFIG = '''\
[irc.server]
host = "irc.acme.test"
port = 6669
ssl = true
password = "EverythingReally!"
rate_limit = 0.5

[irc.bot]
nickname = "syslogger"
realname = "Monsieur Syslog"

[irc]
channels = [
    { name = "#monitoring" },
    { name = "#network" },
    { name = "#serverfarm", password = "more-is-more" },
]

[routes]
514 = [ "#monitoring" ]
10514 = [ "#monitoring", "#network" ]
11514 = [ "#monitoring", "#serverfarm" ]
'''


def test_load_config():
    toml = StringIO(TOML_CONFIG)

    config = load_config(toml)

    assert config.irc == IrcConfig(
        server=IrcServer(
            host='irc.acme.test',
            port=6669,
            ssl=True,
            password='EverythingReally!',
            rate_limit=0.5,
        ),
        nickname='syslogger',
        realname='Monsieur Syslog',
        channels={
            IrcChannel('#monitoring'),
            IrcChannel('#network'),
            IrcChannel('#serverfarm', password='more-is-more'),
        },
    )

    assert config.routes == {
        Route(514, "#monitoring"),
        Route(10514, "#monitoring"),
        Route(10514, "#network"),
        Route(11514, "#monitoring"),
        Route(11514, "#serverfarm"),
    }


TOML_CONFIG_WITH_DEFAULTS = '''\
[irc.server]
host = "irc.organization.test"

[irc.bot]
nickname = "monitor"
'''


def test_load_config_with_defaults():
    toml = StringIO(TOML_CONFIG_WITH_DEFAULTS)

    config = load_config(toml)

    assert config.irc == IrcConfig(
        server=IrcServer(
            host='irc.organization.test',
            port=6667,
            ssl=False,
            password=None,
            rate_limit=None,
        ),
        nickname='monitor',
        realname='syslog',
        channels=set(),
    )

    assert config.routes == set()


TOML_CONFIG_WITHOUT_IRC_SERVER_TABLE = '''\
[irc.bot]
nickname = "monitor"
'''


def test_load_config_without_irc_server_table():
    toml = StringIO(TOML_CONFIG_WITHOUT_IRC_SERVER_TABLE)

    config = load_config(toml)

    assert config.irc.server is None


TOML_CONFIG_WITHOUT_IRC_SERVER_HOST = '''\
[irc.server]

[irc.bot]
nickname = "monitor"
'''


def test_load_config_without_irc_server_host():
    toml = StringIO(TOML_CONFIG_WITHOUT_IRC_SERVER_HOST)

    config = load_config(toml)

    assert config.irc.server is None
