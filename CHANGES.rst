Changelog
=========


Version 0.11
------------

Released 2021-04-21

- Introduced configuration file. Removed the CLI arguments that have
  been replaced by it.

- Moved configuration of IRC channels to join and ports-to-channels
  routes to configuration file.

- Provided an actual ``syslog2irc`` command.

- Published the package to the Python Package Index to allow installing
  from there.

- Added support for IRC server password.

- Added support for a rate limit for the IRC connection, i.e. the
  maximum number of messages per second to send. This can prevent the
  bot from getting kicked (or even banned) from a channel because of
  flooding.

- Added ``Dockerfile``.

- Added command line option ``--version`` to show syslog2IRC's version.


Version 0.10
------------

Released 2021-04-20

- Removed support for unsupported Python versions 2.7, 3.3, 3.4, and
  3.5.

- Added support for Python 3.7, 3.8, and 3.9.

- Split the single module into several modules inside a namespace
  package and a start script. Refactored a lot.

- Added type hints.

- Expect channels in routing configuration to be in sets, not lists.

- A custom formatter for syslog messages can be specified.

- Made bot properly disconnect from IRC with a quit message on shutdown.

- Removed handler to request shutdown via IRC private message.

- Require blinker version 1.4.

- Require irc version 19.0.1.

- Require syslogmp version 0.4.


Version 0.9.1
-------------

Released 2015-09-09

- Exposed programmatic entry point to pass arguments from Python code
  rather than the command line.

- Introduced signal to indicate an approved message. Decoupled processor
  and announcer.

- Wrapped `print` calls in a slightly higher-level, timestamped logging
  function.

- Added and improved tests.

- Created manifest template to package all files relevant for
  distribution.


Version 0.9
-----------

Released 2015-09-08

- Adapted to version 0.2 of syslogmp.

- Spread tests to separate modules.

- Added support to connect to IRC servers via SSL (suggested by Jonas
  Alexandersson).


Version 0.8
-----------

Released 2015-08-10

- Dropped support for Python 3.2.

- The syslog message parser was moved into the new 'syslogmp' package.


Version 0.7
-----------

Released 2014-05-19


Version 0.6
-----------

Released 2014-05-15


Version 0.5
-----------

Released 2013-07-22


Version 0.2–0.4
---------------

unknown


Version 0.1
-----------

Released 2007-04-12
