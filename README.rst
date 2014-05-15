syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Requirements
------------

- Python 2.7+ (tested with 2.7.6) or Python 3.2+ (tested with 3.3.5 and 3.4.0)
- irc_ (tested with 8.9.1)
- blinker_ (tested with 1.3)
- enum34_ (tested with 1.0) on Python versions before 3.4


Installation
------------

irc_ and blinker_ can be installed via pip_:

.. code:: sh

    $ pip install irc blinker

As of Python 3.4, an enum module is part of the standard library. For
older versions of Python, install the enum34_ module:

.. code:: sh

    $ pip install enum34


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

    irc_channel1 = IrcChannel('#examplechannel1')

    routes = {
        514: [irc_channel1],
    }

In a more complex setup, syslog messages could be received on two ports
(514 and 55514), with those received on the first port being forwarded
to two IRC channels, and those received on the letter port being
forwarded exclusively to the second channel.

.. code:: python

    irc_channel1 = IrcChannel('#examplechannel1')
    irc_channel2 = IrcChannel('#examplechannel2', password='zePassword')

    routes = {
          514: [irc_channel1, irc_channel2],
        55514: [irc_channel2],
    }


Usage
-----

You might want to familiarize yourself with the available command line
options first:

.. code:: sh

    $ python syslog2irc.py -h

If no options are given, the IRC component will not be used. Instead,
syslog messages will be written to STDOUT. This is helpful during setup
of syslog message reception. Abort execution by pressing <Control-C>.

.. code:: sh

    $ python syslog2irc.py

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

    $ python syslog2irc.py --irc-server irc.example.com

After a moment, you should see that syslog2IRC has connected to the
server. The IRC bot should then enter the channel(s) you have configured
(see Configuration_).

To use another port on the IRC server than the default (6667), specify
it like this (6669 in this case):

.. code:: sh

    $ python syslog2irc.py --irc-server irc.example.com:6669

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
.. _enum34:   https://pypi.python.org/pypi/enum34
.. _pip:      http://www.pip-installer.org/
.. _IANA:     http://www.iana.org/
.. _RFC 3164: http://tools.ietf.org/html/rfc3164
.. _RFC 5424: http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2014 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 15-May-2014 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
:Version: 0.6
