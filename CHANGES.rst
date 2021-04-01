syslog2IRC Changelog
====================


Version 0.10
------------

not yet released

- Removed support for Python 2.

- Split the single module into several modules inside a namespace
  package and a start script.

- A custom formatter for syslog messages can be specified.

- Shutdown requests per IRC private message can be validated by a custom
  callable, and are disabled by default.

- Support Python 3.5.


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
