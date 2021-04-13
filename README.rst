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

The required packages can be installed via pip_:

.. code:: sh

    $ pip install -r requirements.txt


Configuration
-------------

Setup your ``syslog.conf`` or ``rsyslog.conf`` (commonly found in
``/etc``) to send syslog messages to syslog2IRC on the default syslog
port (514, UDP, as assigned by IANA_)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

Or, when syslog2IRC listens on a non-default port (here: 11514)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on:11514

To specify which IRC channels to join and forward syslog messages to,
create ``IrcChannel`` instances and reference them in the ``routes``
mapping.

A simple routing from the default syslog port, 514, to a single IRC
channel without a password looks like this:

.. code:: python

    channel1 = IrcChannel('#examplechannel1')

    routes = {
        514: [channel1],
    }

In a more complex setup, syslog messages could be received on two ports
(514 and 55514), with those received on the first port being forwarded
to two IRC channels, and those received on the letter port being
forwarded exclusively to the second channel.

.. code:: python

    channel1 = IrcChannel('#examplechannel1')
    channel2 = IrcChannel('#examplechannel2', password='zePassword')

    routes = {
          514: [channel1, channel2],
        55514: [channel2],
    }

For convenience, for example while testing, the bot can be configured to
shut down if a certain text is sent to it as a private message. Just
provide a callable that accepts nickmask and text as positional
arguments and returns a boolean value.

.. code:: python

    def is_shutdown_requested(nickmask, text):
        """Determine if this is a valid shutdown request."""
        return text == 'shutdown!'

    start_with_args(routes, shutdown_predicate=is_shutdown_requested)

Be aware that checking against nickmask and text is not very secure as
they can be faked and guessed, respectively. You might not want to
enable this in a production environment.


Usage
-----

You might want to familiarize yourself with the available command line
options first:

.. code:: sh

    $ python start-syslog2irc.py -h

If no options are given, the IRC component will not be used. Instead,
syslog messages will be written to STDOUT. This is helpful during setup
of syslog message reception. Abort execution by pressing <Control-C>.

.. code:: sh

    $ python start-syslog2irc.py

Send some messages to syslog2IRC using your system's syslog message
sender tool (`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

Note that each message will appear twice on the console syslog2IRC was
started because the handler itself will write it there anyway (so you
have a log on what would be sent to IRC).

If receiving syslog messages works, connect to an IRC server:

.. code:: sh

    $ python start-syslog2irc.py --irc-server irc.example.com

After a moment, you should see that syslog2IRC has connected to the
server. The IRC bot should then enter the channel(s) you have configured
(see Configuration_).

To use another port on the IRC server than the default (6667), specify
it like this (6669 in this case):

.. code:: sh

    $ python start-syslog2irc.py --irc-server irc.example.com:6669

In order to shut down syslog2IRC, send a query message with the text
"shutdown!" to the IRC bot. It should then quit, and syslog2IRC should
exit.


Further Reading
---------------

For more information, see `RFC 3164`_, "The BSD syslog Protocol".

Please note that there is `RFC 5424`_, "The Syslog Protocol", which
obsoletes `RFC 3164`_. syslog2IRC, however, only implements the latter.


.. _irc:      https://bitbucket.org/jaraco/irc
.. _blinker:  http://pythonhosted.org/blinker/
.. _syslogmp: http://homework.nwsnet.de/releases/76d6/#syslogmp
.. _pip:      http://www.pip-installer.org/
.. _IANA:     http://www.iana.org/
.. _RFC 3164: http://tools.ietf.org/html/rfc3164
.. _RFC 5424: http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
