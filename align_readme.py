#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copy the module docstring of syslog2IRC to the README file.
"""

import syslog2irc


with open('README.rst', 'w') as f:
    text = syslog2irc.__doc__.strip()
    f.write(text + '\n')
