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
"""Utilities for multiplatform support of XDG directory handling."""

from __future__ import unicode_literals, print_function

import errno
import os
import sys

__all__ = ['user_home',
           'default_cache_home',
           'default_config_home',
           'default_config_path',
           'default_data_home',
           'default_data_path',
           'get_env_path',
           'get_program_path',
           'unicode_path',
           ]


def _get_exe_path_frozen_win32(exe_name):
    """Get path to the helper .exe on packaged windows."""
    # all the .exes are in the same place on windows:
    cur_exec_path = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(cur_exec_path)
    return os.path.join(exe_dir, exe_name + ".exe")


def _get_exe_path_frozen_darwin(exe_name, app_names):
    """Get path to the sub-app executable on packaged darwin."""

    sub_app_name = app_names[exe_name]
    main_app_dir = "".join(__file__.partition(".app")[:-1])
    main_app_resources_dir = os.path.join(main_app_dir,
                                          "Contents",
                                          "Resources")
    exe_bin = os.path.join(main_app_resources_dir,
                           sub_app_name,
                           "Contents", "MacOS",
                           exe_name)
    return exe_bin


def get_program_path(program_name, *args, **kwargs):
    """Given a program name, returns the path to run that program.

    Raises OSError if the program is not found.

    :param program_name: The name of the program to find. For darwin and win32
        platforms, the behavior is changed slightly, when sys.frozen is set,
        to look in the packaged program locations for the program.
    :param search_dirs: A list of directories to look for the program in. This
        is only available as a keyword argument.
    :param app_names: A dict of program names mapped to sub-app names. Used
        for discovering paths in embedded .app bundles on the darwin platform.
        This is only available as a keyword argument.
    :return: The path to the discovered program.
    """
    search_dirs = kwargs.get('fallback_dirs', None)
    app_names = kwargs.get('app_names', None)

    if getattr(sys, "frozen", None) is not None:
        if sys.platform == 'win32':
            program_path = _get_exe_path_frozen_win32(program_name)
        elif sys.platform == 'darwin':
            program_path = _get_exe_path_frozen_darwin(program_name,
                                                       app_names)
        else:
            raise Exception("Unsupported platform for frozen execution: %r" %
                            sys.platform)
    else:
        if search_dirs is not None:
            for dirname in search_dirs:
                program_path = os.path.join(dirname, program_name)
                if os.path.exists(program_path):
                    return program_path
        else:
            # Check in normal system $PATH, if no fallback dirs specified
            from distutils.spawn import find_executable
            program_path = find_executable(program_name)

    if program_path is None or not os.path.exists(program_path):
        raise OSError(errno.ENOENT,
                      "Could not find executable %r" % program_name)

    return program_path


def get_env_path(key, default):
    """Get a UTF-8 encoded path from an environment variable."""
    if key in os.environ:
        # on windows, environment variables are mbcs bytes
        # so we must turn them into utf-8 Syncdaemon paths
        try:
            path = os.environb.get(key.encode('utf-8'))
        except AttributeError:
            path = os.environ[key]
        return path.decode(sys.getfilesystemencoding()).encode('utf-8')
    else:
        if not isinstance(default, bytes):
            return default.encode('utf-8')
        return default


def unicode_path(utf8path):
    """Turn an utf8 path into a unicode path."""
    if isinstance(utf8path, bytes):
        return utf8path.decode("utf-8")
    return utf8path


def get_special_folders():
    """ Routine to grab all the Windows Special Folders locations.

    If successful, returns dictionary
    of shell folder locations indexed on Windows keyword for each;
    otherwise, returns an empty dictionary.
    """
    # pylint: disable=W0621, F0401, E0611
    special_folders = {}

    if sys.platform == 'win32':
        from win32com.shell import shell, shellcon
        # CSIDL_LOCAL_APPDATA = C:\Users\<username>\AppData\Local
        # CSIDL_PROFILE = C:\Users\<username>
        # CSIDL_COMMON_APPDATA = C:\ProgramData
        # More information on these constants at
        # http://msdn.microsoft.com/en-us/library/bb762494

        # per http://msdn.microsoft.com/en-us/library/windows/desktop/bb762181,
        # SHGetFolderPath is deprecated, replaced by SHGetKnownFolderPath
        # (http://msdn.microsoft.com/en-us/library/windows/desktop/bb762188)
        get_path = lambda name: shell.SHGetFolderPath(
            0, getattr(shellcon, name), None, 0).encode('utf8')
        special_folders['Personal'] = get_path("CSIDL_PROFILE")
        special_folders['Local AppData'] = get_path("CSIDL_LOCAL_APPDATA")
        special_folders['AppData'] = os.path.dirname(
            special_folders['Local AppData'])
        special_folders['Common AppData'] = get_path("CSIDL_COMMON_APPDATA")

    return special_folders


# pylint: disable=C0103
if sys.platform == 'win32':
    special_folders = get_special_folders()
    user_home = special_folders['Personal']
    default_config_path = special_folders['Common AppData']
    default_config_home = special_folders['Local AppData']
    default_data_path = os.path.join(default_config_path, b'xdg')
    default_data_home = os.path.join(default_config_home, b'xdg')
    default_cache_home = os.path.join(default_data_home, b'cache')
elif sys.platform == 'darwin':
    user_home = os.path.expanduser(b'~')
    default_cache_home = os.path.join(user_home, b'Library', b'Caches')
    default_config_path = b'/Library/Preferences:/etc/xdg'
    default_config_home = os.path.join(user_home, b'Library', b'Preferences')
    default_data_path = b':'.join([b'/Library/Application Support',
                                  b'/usr/local/share',
                                  b'/usr/share'])
    default_data_home = os.path.join(user_home, b'Library',
                                     b'Application Support')
else:
    user_home = os.path.expanduser(b'~')
    default_cache_home = os.path.join(user_home,
                                      b'.cache')
    default_config_path = b'/etc/xdg'
    default_config_home = os.path.join(user_home,
                                       b'.config')
    default_data_path = b'/usr/local/share:/usr/share'
    default_data_home = os.path.join(user_home,
                                     b'.local', b'share')
