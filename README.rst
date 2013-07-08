syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.


Installation
------------

Needs Python 2.7+ or Python 3+ (tested with 3.3.2).

Also requires the `python-irclib`_ package (tested with 8.3.1), which can be
installed via pip_:

.. code:: sh

    $ pip install irc


Configuration
-------------

Setup your ``syslog.conf`` or ``rsyslog.conf`` (commonly found in ``/etc``) to
send syslog messages to syslog2IRC on the default syslog port (514, UDP, as
assigned by IANA_)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on

Or, when syslog2IRC listens on a non-default port (here: 11514)::

    *.*     @host-to-send-log-messages-to-and-this-script-runs-on:11514

To specify the IRC channels to join, adjust the list ``IRC_CHANNELS``, which
is expected to contain (channel name, password) pairs.


Usage
-----

You might want to familiarze yourself with the available command line options
first:

.. code:: sh

    $ python syslog2irc.py -h

If no options are given, the IRC component will not be used. Instead, syslog
messages will be written to STDOUT. This is helpful during setup of syslog
message reception.

.. code:: sh

    $ python syslog2irc.py

If the syslog deamon is configured to forward to a port other than the
default, specify that:

.. code:: sh

    $ python syslog2irc.py --syslog-port 11514

Send some messages to syslog2IRC using your system's syslog message sender tool
(`logger`, in this example):

.. code:: sh

    $ logger 'Hi there!'
    $ logger -p kern.alert 'Whoa!'

Note that each message will appear twice on the console syslog2IRC was started
because the handler itself will write it there anyway (so you have a log on
what would be sent to IRC).

If receiving syslog messages works, connect to an IRC server:

.. code:: sh

    $ python syslog2irc.py irc.example.com

After a moment, you should see that syslog2IRC has connected to the server.
The IRC bot should then enter the channel(s) you have configured (see
Configuration_).

To use another port on the IRC server than the default (6667), specify it like
this (6669 in this case):

.. code:: sh

    $ python syslog2irc.py irc.example.com:6669

In order to shut down syslog2IRC, send a query message with the text
"shutdown!" to the IRC bot. It should then quit, and syslog2IRC should exit.


Further Reading
---------------

For more information, see `RFC 3164`_, "The BSD syslog Protocol".

Please note that there is `RFC 5424`_, "The Syslog Protocol", which obsoletes
`RFC 3164`_. syslog2IRC, however, only implements the latter.


.. _python-irclib:  http://python-irclib.sourceforge.net/
.. _pip:            http://www.pip-installer.org/
.. _IANA:           http://www.iana.org/
.. _RFC 3164:       http://tools.ietf.org/html/rfc3164
.. _RFC 5424:       http://tools.ietf.org/html/rfc5424


:Copyright: 2007-2013 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 09-Jul-2013 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
