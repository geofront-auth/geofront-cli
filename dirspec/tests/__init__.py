# -*- coding: utf-8 -*-
#
# Copyright 2011-2012 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
""""dirspec tests."""

from __future__ import unicode_literals, print_function

import os

from operator import setitem
from testtools.testcase import TestCase


class BaseTestCase(TestCase):
    """Base test case for dirspect tests."""

    def assert_utf8_bytes(self, value):
        """Check that 'value' is a bytes sequence encoded with utf-8."""
        self.assertIsInstance(value, bytes)
        try:
            value.decode('utf-8')
        except UnicodeError:
            self.fail('%r should be a utf8 encoded string.' % value)

    def tweak_env(self, envvar, value):
        """Tweak the environment variable %var to %value.

        Restore the old value when finished.
        """
        old_val = os.environ.get(envvar, None)

        if old_val is None:
            self.addCleanup(os.environ.pop, envvar, None)
        else:
            self.addCleanup(setitem, os.environ, envvar, old_val)
        if value is None:
            os.environ.pop(envvar, None)
        else:
            os.environ[envvar] = value
