"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from io import StringIO

from syslog2irc.config import load_config
from syslog2irc.irc import IrcChannel, IrcConfig, IrcServer
from syslog2irc.network import Port, TransportProtocol
from syslog2irc.routing import Route


TOML_CONFIG = '''\
log_level = "warning"

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
commands = [
  "MODE syslogger +i",
]
channels = [
    { name = "#monitoring" },
    { name = "#network" },
    { name = "#serverfarm", password = "more-is-more" },
]

[routes]
"514/udp" = [ "#monitoring" ]
"10514/udp" = [ "#monitoring", "#network" ]
"11514/tcp" = [ "#monitoring", "#serverfarm" ]
'''


def test_load_config():
    toml = StringIO(TOML_CONFIG)

    config = load_config(toml)

    assert config.log_level == 'WARNING'

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
        commands=[
            'MODE syslogger +i',
        ],
        channels={
            IrcChannel('#monitoring'),
            IrcChannel('#network'),
            IrcChannel('#serverfarm', password='more-is-more'),
        },
    )

    assert config.routes == {
        Route(Port(514, TransportProtocol.UDP), "#monitoring"),
        Route(Port(10514, TransportProtocol.UDP), "#monitoring"),
        Route(Port(10514, TransportProtocol.UDP), "#network"),
        Route(Port(11514, TransportProtocol.TCP), "#monitoring"),
        Route(Port(11514, TransportProtocol.TCP), "#serverfarm"),
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

    assert config.log_level == 'DEBUG'

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
        commands=[],
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
