syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Requirements
------------

- Python 3.7+
- irc_
- blinker_
- syslogmp_


Installation
------------

syslog2IRC and its dependencies can be installed via pip_:

.. code:: sh

    $ pip install syslog2irc


Configuration
-------------


syslog
++++++

Setup your ``syslog.conf`` or ``rsyslog.conf`` (commonly found in
``/etc``) to send syslog messages to syslog2IRC on the default syslog
port (514, UDP, as assigned by IANA_)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

Or, when syslog2IRC listens on a non-default port (here: 11514)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on:11514


syslog2IRC
++++++++++

An example configuration file, ``config.toml``, in TOML_ format:

.. code:: toml

    [irc.server]
    host = "irc.server.example"  # optional
    port = 6667                  # optional
    ssl = false                  # optional
    password = "t0ps3cr3t"       # optional
    rate_limit = 0.5             # optional; limit of messages per second

    [irc.bot]
    nickname = "syslog"
    realname = "syslog"          # optional

    [irc]
    channels = [
      { name = "#examplechannel1" },
      { name = "#examplechannel2", password = "zePassword" },
    ]

    [routes]
    # routing for syslog messages from the ports on which they are
    # received to the IRC channels they should be announced on
    514 = [ '#examplechannel1' ]
    55514 = [ '#examplechannel2' ]

.. _TOML: https://toml.io/

A simple routing from the default syslog port, 514, to a single IRC
channel would look like this:

.. code:: toml

    [routes]
    514 = [ '#examplechannel1' ]

In a more complex setup, syslog messages could be received on two ports
(514 and 55514 in this example), with those received on the first port
being forwarded to two IRC channels, and those received on the latter
port being forwarded exclusively to the second channel.

.. code:: toml

    [routes]
    514 = [ '#examplechannel1', '#examplechannel2' ]
    55514 = [ '#examplechannel2' ]


IRC Dummy Mode
--------------

If no value for ``irc.server.host`` is set (the property is missing or
commented out), syslog2IRC will not attempt to connect to an IRC server
and start in IRC dummy mode.

In this mode, it will still receive syslog messages, but it will write
them to STDOUT. This can be helpful during setup of syslog message
reception.

Abort execution by pressing <Control-C>.


Usage
-----

Start syslog2IRC with a configuration file:

.. code:: sh

    $ syslog2irc config.toml

Send some messages to syslog2IRC using your system's syslog message
sender tool (`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

Note that each message will appear twice on the console syslog2IRC was
started because the handler itself will write it there anyway (so you
have a log on what would be sent to IRC).

If receiving syslog messages works and you have been using IRC dummy
mode so far, specify an IRC server in the configuration file, then start
as above:

.. code:: sh

    $ syslog2irc config.toml

After a moment, you should see that syslog2IRC has connected to the IRC
server. The bot should then enter the channel(s) you have configured
(see Configuration_).


Further Reading
---------------

For more information, see `RFC 3164`_, "The BSD syslog Protocol".

Please note that there is `RFC 5424`_, "The Syslog Protocol", which
obsoletes `RFC 3164`_. syslog2IRC, however, only implements the latter.


.. _irc:      https://bitbucket.org/jaraco/irc
.. _blinker:  https://pythonhosted.org/blinker/
.. _syslogmp: https://homework.nwsnet.de/releases/76d6/#syslogmp
.. _pip:      http://www.pip-installer.org/
.. _IANA:     https://www.iana.org/
.. _RFC 3164: https://tools.ietf.org/html/rfc3164
.. _RFC 5424: https://tools.ietf.org/html/rfc5424


:Copyright: 2007-2021 `Jochen Kupperschmidt <https://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
