""":mod:`geofrontcli.version` --- Version data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function


#: (:class:`tuple`) The triple of version numbers e.g. ``(1, 2, 3)``.
VERSION_INFO = (0, 3, 3)

#: (:class:`str`) The version string e.g. ``'1.2.3'``.
VERSION = '{0}.{1}.{2}'.format(*VERSION_INFO)

#: (:class:`tuple`) The minimum compatible version of server protocol.
MIN_PROTOCOL_VERSION = (0, 2, 0)

#: (:class:`tuple`) The maximum compatible version of server protocol.
MAX_PROTOCOL_VERSION = (0, 4, 999)


if __name__ == '__main__':
    print(VERSION)
