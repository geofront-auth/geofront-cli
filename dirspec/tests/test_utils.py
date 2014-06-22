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
"""Tests for utilities for the base directory implementation."""

from __future__ import unicode_literals, print_function

import os
import sys

from dirspec import basedir, utils as dirutils
from dirspec.utils import (get_env_path, get_special_folders,
                           user_home, get_program_path)
from dirspec.tests import BaseTestCase
from testtools.testcase import skip


class UtilsTestCase(BaseTestCase):
    """Test for the multiplatform directory utilities."""

    def test_user_home_is_utf8_bytes(self):
        """The returned path is bytes."""
        actual = user_home
        self.assert_utf8_bytes(actual)


class FakeShellConModule(object):
    """Override CSIDL_ constants."""

    CSIDL_PROFILE = 0
    CSIDL_LOCAL_APPDATA = 1
    CSIDL_COMMON_APPDATA = 2


class FakeShellModule(object):

    """Fake Shell Module."""

    def __init__(self):
        """Set the proper mapping between CSIDL_ consts."""
        self.values = {
            0: 'c:\\path\\to\\users\\home',
            1: 'c:\\path\\to\\users\\home\\appData\\local',
            2: 'c:\\programData',
        }

    # pylint: disable=C0103
    def SHGetFolderPath(self, dummy0, shellconValue, dummy2, dummy3):
        """Override SHGetFolderPath functionality."""
        return self.values[shellconValue]
    # pylint: enable=C0103


class TestBaseDirectoryWindows(BaseTestCase):
    """Tests for the BaseDirectory module."""

    def test_get_special_folders(self):
        """Make sure we can import the platform module."""
        if sys.platform != 'win32':
            self.skipTest('Win32 is required for this test.')

        import win32com.shell
        shell_module = FakeShellModule()
        self.patch(win32com.shell, "shell", shell_module)
        self.patch(win32com.shell, "shellcon", FakeShellConModule())
        special_folders = get_special_folders()
        self.assertTrue('Personal' in special_folders)
        self.assertTrue('Local AppData' in special_folders)
        self.assertTrue('AppData' in special_folders)
        self.assertTrue('Common AppData' in special_folders)

        self.assertEqual(
            special_folders['Personal'],
            shell_module.values[FakeShellConModule.CSIDL_PROFILE])
        self.assertEqual(
            special_folders['Local AppData'],
            shell_module.values[FakeShellConModule.CSIDL_LOCAL_APPDATA])
        self.assertTrue(
            special_folders['Local AppData'].startswith(
                special_folders['AppData']))
        self.assertEqual(
            special_folders['Common AppData'],
            shell_module.values[FakeShellConModule.CSIDL_COMMON_APPDATA])

        for val in special_folders.itervalues():
            self.assertIsInstance(val, str)
            val.encode('utf-8')

    def test_get_data_dirs(self):
        """Check thet get_data_dirs uses pathsep correctly."""
        bad_sep = str(filter(lambda x: x not in os.pathsep, ":;"))
        dir_list = ["A", "B", bad_sep, "C"]
        self.tweak_env('XDG_DATA_DIRS', os.pathsep.join(dir_list))
        dirs = basedir.get_xdg_data_dirs()[1:]
        self.assertEqual(dirs, [x.encode('utf-8') for x in dir_list])

    def test_get_config_dirs(self):
        """Check thet get_data_dirs uses pathsep correctly."""
        bad_sep = str(filter(lambda x: x not in os.pathsep, ":;"))
        dir_list = ["A", "B", bad_sep, "C"]
        self.tweak_env('XDG_CONFIG_DIRS', os.pathsep.join(dir_list))
        dirs = basedir.get_xdg_config_dirs()[1:]
        self.assertEqual(dirs, [x.encode('utf-8') for x in dir_list])

    def unset_fake_environ(self, key):
        """Unset (and restore) a fake environ variable."""
        if key in os.environ:
            current_value = os.environ[key]
            self.addCleanup(os.environ.__setitem__, key, current_value)
            del(os.environ[key])

    @skip('UnicodeEncodeError: bug #907053')
    def test_get_env_path_var(self):
        """Test that get_env_path transforms an env var."""
        fake_path = 'C:\\Users\\Ñandú'
        fake_env_var = 'FAKE_ENV_VAR'

        mbcs_path = fake_path.encode(sys.getfilesystemencoding())

        self.tweak_env(fake_env_var, str(mbcs_path))
        self.assertEqual(get_env_path(fake_env_var, "unexpected"), fake_path)

    @skip('UnicodeEncodeError: bug #907053')
    def test_get_env_path_no_var(self):
        """Test that get_env_path returns the default when env var not set."""
        fake_path = "C:\\Users\\Ñandú"
        fake_env_var = "fake_env_var"
        default = fake_path.encode(sys.getfilesystemencoding())

        self.unset_fake_environ(fake_env_var)
        self.assertEqual(get_env_path(fake_env_var, default), default)


class ProgramPathBaseTestCase(BaseTestCase):
    """Base class for testing the executable finder."""

    def setUp(self):
        """Set up fake modules."""
        super(ProgramPathBaseTestCase, self).setUp()
        self.patch(os.path, "exists", lambda x: True)


class UnfrozenSrcTestCase(ProgramPathBaseTestCase):
    """Test non-linux path discovery."""

    def setUp(self):
        super(UnfrozenSrcTestCase, self).setUp()
        self.patch(sys, "platform", "darwin")

    def test_unfrozen_dev_toplevel(self):
        """Not frozen, return path to bin dir."""
        path = get_program_path("foo", fallback_dirs=['/path/to/bin'])
        self.assertEquals(path, os.path.join("/path/to/bin", "foo"))

    def test_unfrozen_dev_toplevel_raises_nopath(self):
        """Not frozen, raise OSError when the path doesn't exist."""
        self.patch(os.path, "exists", lambda x: False)
        self.assertRaises(OSError, get_program_path, "foo")


class DarwinPkgdTestCase(ProgramPathBaseTestCase):
    """Test cmdline for running packaged on darwin."""

    def setUp(self):
        """SetUp to mimic frozen darwin."""
        super(DarwinPkgdTestCase, self).setUp()
        self.patch(sys, "platform", "darwin")
        sys.frozen = True

        self.darwin_app_names = {"foo": "Foo.app"}

    def tearDown(self):
        """tearDown, Remove frozen attr"""
        del sys.frozen
        super(DarwinPkgdTestCase, self).tearDown()

    def test_darwin_pkgd(self):
        """Return sub-app path on darwin when frozen."""
        path = get_program_path("foo", app_names=self.darwin_app_names)
        expectedpath = "%s%s" % (
            dirutils.__file__,
            os.path.sep + os.path.join('Contents', 'Resources', 'Foo.app',
                                       'Contents', 'MacOS', 'foo'))
        self.assertEquals(path, expectedpath)

    def test_darwin_pkgd_raises_on_no_appnames(self):
        """Raises TypeError when no app_names dict is in the kwargs."""
        self.assertRaises(TypeError, get_program_path, "foo")

    def test_darwin_pkgd_raises_nopath(self):
        """Frozen, raise OSError when the path doesn't exist."""
        self.patch(os.path, "exists", lambda x: False)
        self.assertRaises(OSError, get_program_path, "foo",
                          app_names=self.darwin_app_names)


class Win32PkgdTestCase(ProgramPathBaseTestCase):
    """Test cmdline for running packaged on windows."""

    def setUp(self):
        """SetUp to mimic frozen windows."""
        super(Win32PkgdTestCase, self).setUp()
        self.patch(sys, "platform", "win32")
        sys.frozen = True

    def tearDown(self):
        """tearDown, Remove frozen attr"""
        del sys.frozen
        super(Win32PkgdTestCase, self).tearDown()

    def test_windows_pkgd(self):
        """Return sub-app path on windows when frozen."""

        self.patch(sys, "executable", os.path.join("C:\\path", "to",
                                                   "current.exe"))
        # patch abspath to let us run this tests on non-windows:
        self.patch(os.path, "abspath", lambda x: x)
        path = get_program_path("foo", None)
        expectedpath = os.path.join("C:\\path", "to", "foo.exe")
        self.assertEquals(path, expectedpath)

    def test_windows_pkgd_raises_nopath(self):
        """Frozen, raise OSError when the path doesn't exist."""
        self.patch(os.path, "exists", lambda x: False)
        self.assertRaises(OSError, get_program_path, "foo")


class PosixTestCase(ProgramPathBaseTestCase):
    """Test cmdline for running on linux."""

    def setUp(self):
        """SetUp to mimic linux2."""
        super(PosixTestCase, self).setUp()
        self.patch(sys, "platform", "linux2")

    def test_linux_src_relative_path_exists(self):
        """linux, return source relative path if it exists."""
        path = get_program_path("foo", fallback_dirs=['/path/to/bin'])
        expectedpath = os.path.join("/path/to/bin", "foo")
        self.assertEquals(path, expectedpath)

    def test_linux_no_src_relative_path(self):
        """raise if no src rel path."""
        self.patch(os.path, "exists", lambda x: False)
        self.assertRaises(OSError, get_program_path, "foo")
