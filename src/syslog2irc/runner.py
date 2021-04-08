"""
syslog2irc.runner
~~~~~~~~~~~~~~~~~

A looping, stoppable runner

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from time import sleep

from .util import log


class Runner(object):
    def __init__(self):
        self.shutdown = False

    def request_shutdown(self, sender):
        self.shutdown = True

    def run(self, seconds_to_sleep=0.5):
        """Run the main loop until shutdown is requested."""
        while not self.shutdown:
            sleep(seconds_to_sleep)

        log('Shutting down ...')
