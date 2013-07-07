# -*- coding: utf-8 -*-

"""
Tests for syslog2IRC
====================


Requirements
------------

- Python 2.6+ or Python 3.2+
- nose2_ (tested with version 0.4.6)


Installation
------------

Install nose2_:

.. code:: sh

    $ pip install nose2


Usage
-----

Run the tests (attention: do *not* specify the `.py` extension, just the
module name!):

.. code:: sh

    $ nose2 test_syslog2irc


.. _nose2: https://github.com/nose-devs/nose2


:Copyright: 2007-2013 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 07-Jul-2013
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from datetime import datetime
import unittest

from nose2.tools import params

from syslog2irc import SyslogMessage, SyslogMessageParser


CURRENT_YEAR = datetime.today().year

@params(
    (
        # Example 1 from RFC 3164.
        '<34>Oct 11 22:14:15 mymachine su: \'su root\' failed for lonvick on /dev/pts/8',
        4,
        'security/authorization messages',
        2,
        'Critical',
        datetime(CURRENT_YEAR, 10, 11, 22, 14, 15),
        'mymachine',
        'su: \'su root\' failed for lonvick on /dev/pts/8',
    ),
    (
        # Example 2 from RFC 3164.
        '<13>Feb  5 17:32:18 10.0.0.99 Use the BFG!',
        1,
        'user-level messages',
        5,
        'Notice',
        datetime(CURRENT_YEAR, 2, 5, 17, 32, 18),
        '10.0.0.99',
        'Use the BFG!',
    ),
    (
        # Example 3 from RFC 3164.
        # Note that the HOSTNAME and MSG fields in this example are not
        # consistent with what the RFC defines.
        '<165>Aug 24 05:34:00 CST 1987 mymachine myproc[10]: %% It\'s time to make the do-nuts.  %%  Ingredients: Mix=OK, Jelly=OK # Devices: Mixer=OK, Jelly_Injector=OK, Frier=OK # Transport: Conveyer1=OK, Conveyer2=OK # %%',
        20,
        'local use 4 (local4)',
        5,
        'Notice',
        datetime(CURRENT_YEAR, 8, 24, 5, 34, 0),
        'CST',
        '1987 mymachine myproc[10]: %% It\'s time to make the do-nuts.  %%  Ingredients: Mix=OK, Jelly=OK # Devices: Mixer=OK, Jelly_Injector=OK, Frier=OK # Transport: Conveyer1=OK, Conveyer2=OK # %%',
    ),
        # Example 4 from RFC 3164.
        # This cannot be parsed because the format of the TIMESTAMP field
        # is invalid.
        #'<0>1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
    (
        # Example 5 from RFC 3164.
        '<0>Oct 22 10:52:12 scapegoat 1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
        0,
        'kernel messages',
        0,
        'Emergency',
        datetime(CURRENT_YEAR, 10, 22, 10, 52, 12),
        'scapegoat',
        '1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
    ),
)
def test_syslog_message_parser(
        data,
        expected_facility_id,
        expected_facility_name,
        expected_severity_id,
        expected_severity_name,
        expected_timestamp,
        expected_hostname,
        expected_message):
    actual = SyslogMessageParser.parse(data)
    assert actual.facility_id == expected_facility_id
    assert actual.facility_name == expected_facility_name
    assert actual.severity_id == expected_severity_id
    assert actual.severity_name == expected_severity_name
    assert actual.timestamp == expected_timestamp
    assert actual.hostname == expected_hostname
    assert actual.message == expected_message
