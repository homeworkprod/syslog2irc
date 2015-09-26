syslog2IRC Changelog
====================


Version 0.10
------------

not yet released

- Split the single module into several modules inside a namespace
  package and a start script.
- Shutdown requests per IRC private message can be validated by a custom
  callable, and are disabled by default.
- Support Python 3.5.


Version 0.9.1
-------------

Released September 9, 2015

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

Released September 8, 2015

- Adapted to version 0.2 of syslogmp.
- Spread tests to separate modules.
- Added support to connect to IRC servers via SSL (suggested by Jonas
  Alexandersson).


Version 0.8
-----------

Released August 10, 2015

- Dropped support for Python 3.2.
- The syslog message parser was moved into the new 'syslogmp' package.


Version 0.7
-----------

Released May 19, 2014


Version 0.6
-----------

Released May 15, 2014


Version 0.5
-----------

Released July 22, 2013


Version 0.2–0.4
---------------

unknown


Version 0.1
-----------

Released April 12, 2007
