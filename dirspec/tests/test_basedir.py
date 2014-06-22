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
"""Tests for the base directory implementation."""

from __future__ import unicode_literals, print_function

import os

from dirspec import basedir
from dirspec.tests import BaseTestCase


class BasedirTestCase(BaseTestCase):
    """Tests for XDG Base Directory paths implementation."""

    def test_cache_home(self):
        """Test that XDG_CACHE_HOME is handled correctly."""
        self.tweak_env('XDG_CACHE_HOME',
                       os.path.abspath(os.path.join(os.getcwd(),
                                                    '_trial_temp',
                                                    'cache')))
        self.assertEqual(os.environ['XDG_CACHE_HOME'].encode('utf-8'),
                         basedir.get_xdg_cache_home())

    def test_config_dirs(self):
        """Test that XDG_CONFIG_HOME is handled correctly."""
        self.tweak_env('XDG_CONFIG_HOME',
                       os.path.abspath(os.path.join(os.getcwd(),
                                                    '_trial_temp',
                                                    'config')))
        self.tweak_env('XDG_CONFIG_DIRS', os.pathsep.join(['etc']))
        self.assertEqual([os.environ['XDG_CONFIG_HOME'].encode('utf-8'),
                          b'etc'],
                         basedir.get_xdg_config_dirs())

    def test_config_home(self):
        """Test that XDG_CONFIG_DIRS is handled correctly."""
        self.tweak_env('XDG_CONFIG_HOME',
                       os.path.abspath(os.path.join(os.getcwd(),
                                                    '_trial_temp',
                                                    'config')))
        self.assertEqual(os.environ['XDG_CONFIG_HOME'].encode('utf-8'),
                         basedir.get_xdg_config_home())

    def test_data_dirs(self):
        """Test that XDG_DATA_HOME is handled correctly."""
        self.tweak_env('XDG_DATA_HOME',
                       os.path.abspath(os.path.join(os.getcwd(),
                                                    '_trial_temp',
                                                    'xdg_data')))
        self.tweak_env('XDG_DATA_DIRS', os.pathsep.join(['foo', 'bar']))
        self.assertEqual([os.environ['XDG_DATA_HOME'].encode('utf-8'),
                          b'foo', b'bar'],
                         basedir.get_xdg_data_dirs())

    def test_data_home(self):
        """Test that XDG_DATA_HOME is handled correctly."""
        self.tweak_env('XDG_DATA_HOME',
                       os.path.abspath(os.path.join(os.getcwd(),
                                                    '_trial_temp',
                                                    'xdg_data')))
        self.assertEqual(os.environ['XDG_DATA_HOME'].encode('utf-8'),
                         basedir.get_xdg_data_home())

    def test_default_cache_home(self):
        """Ensure default values work correctly."""
        self.tweak_env('XDG_CACHE_HOME', None)
        expected = b'/blah'
        self.patch(basedir, 'default_cache_home', expected)
        self.assertFalse(os.environ.get('XDG_CACHE_HOME', False))
        self.assertEqual(basedir.get_xdg_cache_home(), expected)

    def test_default_config_dirs(self):
        """Ensure default values work correctly."""
        self.tweak_env('XDG_CONFIG_DIRS', None)
        self.tweak_env('XDG_CONFIG_HOME', None)
        expected = b'/blah'
        self.patch(basedir, 'default_config_home', expected)
        self.patch(basedir, 'default_config_path', '')
        self.assertFalse(os.environ.get('XDG_CONFIG_DIRS', False))
        self.assertFalse(os.environ.get('XDG_CONFIG_HOME', False))
        self.assertEqual(basedir.get_xdg_config_dirs(), [expected, b''])

    def test_default_config_home(self):
        """Ensure default values work correctly."""
        self.tweak_env('XDG_CONFIG_HOME', None)
        expected = b'/blah'
        self.patch(basedir, 'default_config_home', expected)
        self.assertFalse(os.environ.get('XDG_CONFIG_HOME', False))
        self.assertEqual(basedir.get_xdg_config_home(), expected)

    def test_default_data_dirs(self):
        """Ensure default values work correctly."""
        self.tweak_env('XDG_DATA_DIRS', None)
        self.tweak_env('XDG_DATA_HOME', None)
        expected = b'/blah'
        self.patch(basedir, 'default_data_home', expected)
        self.patch(basedir, 'default_data_path', '')
        self.assertFalse(os.environ.get('XDG_DATA_DIRS', False))
        self.assertFalse(os.environ.get('XDG_DATA_HOME', False))
        self.assertEqual(basedir.get_xdg_data_dirs(), [expected, b''])

    def test_default_data_home(self):
        """Ensure default values work correctly."""
        self.tweak_env('XDG_DATA_HOME', None)
        expected = b'/blah'
        self.patch(basedir, 'default_data_home', expected)
        self.assertFalse(os.environ.get('XDG_DATA_HOME', False))
        self.assertEqual(basedir.get_xdg_data_home(), expected)

    def test_xdg_cache_home_is_utf8_bytes(self):
        """The returned path is bytes."""
        actual = basedir.xdg_cache_home
        self.assert_utf8_bytes(actual)

    def test_xdg_config_home_is_utf8_bytes(self):
        """The returned path is bytes."""
        actual = basedir.xdg_config_home
        self.assert_utf8_bytes(actual)

    def test_xdg_config_dirs_are_bytes(self):
        """The returned path is bytes."""
        result = basedir.xdg_config_dirs
        for actual in result:
            self.assert_utf8_bytes(actual)

    def test_xdg_data_home_is_utf8_bytes(self):
        """The returned path is bytes."""
        actual = basedir.xdg_data_home
        self.assert_utf8_bytes(actual)

    def test_xdg_data_dirs_are_bytes(self):
        """The returned path is bytes."""
        result = basedir.xdg_data_dirs
        for actual in result:
            self.assert_utf8_bytes(actual)

    def test_load_config_paths_filter(self):
        """Since those folders don't exist, this should be empty."""
        self.assertEqual(list(basedir.load_config_paths("x")), [])

    def test_save_config_path(self):
        """The path should end with xdg_config/x (respecting the separator)."""
        self.tweak_env('XDG_CONFIG_HOME', 'config_home')
        self.patch(os, "makedirs", lambda *args: None)
        result = basedir.save_config_path("x")
        self.assertEqual(result.decode('utf-8').split(os.sep)[-2:],
                         ['config_home', 'x'])
