Geofront CLI client
===================

.. image:: https://badge.fury.io/py/geofront-cli.svg?
   :target: https://pypi.python.org/pypi/geofront-cli
   :alt: Latest PyPI version

.. image:: https://travis-ci.org/spoqa/geofront-cli.svg?
   :target: https://travis-ci.org/spoqa/geofront-cli
   :alt: Build status (Travis CI)

.. image:: https://ci.appveyor.com/api/projects/status/wjcgay1b4twffwbc?svg=true
   :target: https://ci.appveyor.com/project/dahlia/geofront-cli
   :alt: Build status (AppVeyor)

It provides a CLI client for Geofront_, a simple SSH key management server.

.. _Geofront: https://geofront.readthedocs.org/


Installation
------------

It is available on PyPI__, so you can install it using ``pip`` installer.
We, however, recommend to use pipsi_ instead so that geofront-cli and its
dependencies don't make your global site-packages messy.

.. code-block:: console

   $ pipsi install geofront-cli

__ https://pypi.python.org/pypi/geofront-cli
.. _pipsi: https://github.com/mitsuhiko/pipsi


Getting started
---------------

What you have to do first of all is to configure the Geofront server URL.
Type ``geofront-cli start`` and then it will show a prompt:

.. code-block:: console

   $ geofront-cli start
   Geofront server URL:

We suppose ``http://example.com/`` here.  It will open an authentication
page in your default web browser:

.. code-block:: console

   $ geofront-cli start
   Geofront server URL: http://example.com/
   Continue to authenticate in your web browser...
   Press return to continue


List available remotes
----------------------

You can list the available remotes using ``geofront-cli remotes`` command:

.. code-block:: console

   $ geofront-cli remotes
   web-1
   web-2
   web-3
   worker-1
   worker-2
   db-1
   db-2

If you give ``-v``/``--verbose`` option it will show their actual addresses
as well:

.. code-block:: console

   $ geofront-cli remotes -v
   web-1	ubuntu@192.168.0.5
   web-2	ubuntu@192.168.0.6
   web-3	ubuntu@192.168.0.7
   worker-1	ubuntu@192.168.0.25
   worker-2	ubuntu@192.168.0.26
   db-1	ubuntu@192.168.0.50
   db-2	ubuntu@192.168.0.51


SSH to remote
-------------

You can easily connect to a remote through SSH.  Use ``geofront-cli ssh``
command instead of vanilla ``ssh``:

.. code-block:: console

   $ geofront-cli ssh web-1
   Welcome to Ubuntu 12.04.3 LTS (GNU/Linux 2.6.32-042stab078.27 i686)

    * Documentation:  https://help.ubuntu.com/
   ubuntu@web-1:~$ 

In most cases, you probably need to list remotes to find an alias to SSH
before run ``geofront-cli ssh`` command.  ``geofront-cli go`` command is
a single command for these two actions at once:

.. code-block:: console

   $ geofront-cli go
   (...interactive fuzzy finder for remotes is shown...)
   Welcome to Ubuntu 12.04.3 LTS (GNU/Linux 2.6.32-042stab078.27 i686)

    * Documentation:  https://help.ubuntu.com/
   ubuntu@web-1:~$ 

Note that there's a shortcut command ``gfg`` which is an alias of
``geofront-cli go``.

There is ``geofront-cli scp`` command as well, which is corresponding
to ``scp``:

.. code-block:: console

   $ geofront-cli scp file.txt web-1:file.txt
   file.txt                                      100% 3157     3.1KB/s   00:00
   $ geofront-cli scp -r web-1:path/etc/apt ./
   sources.list                                  100% 3157     3.1KB/s   00:00
   trusted.gpg                                   100%   14KB  13.9KB/s   00:00


Missing features
----------------

- Shortcut for ``geofront-cli ssh`` command
- Make ``geofront-cli ssh`` similar to ``ssh``
- Autocompletion


Author and license
------------------

`Hong Minhee`__ wrote geofront-cli, and Spoqa_ maintains it.
It is licensed under GPLv3_ or later.

__ https://hongminhee.org/
.. _Spoqa: http://www.spoqa.com/
.. _GPLv3: http://www.gnu.org/licenses/gpl-3.0.html


Changelog
---------

Version 0.4.4
`````````````

Released on April 03, 2020.

- Fixed some command won't work properly.
  This bug occured when running ssh or scp command through the other command.
  (e.g. `geofront-cli go`) [`#19`__ by cynthia]

__ https://github.com/spoqa/geofront-cli/pull/19

Version 0.4.3
`````````````

Released on March 25, 2020.

- Added jump host options to use ProxyJump in SSH. [`#18`__ by cynthia]

__ https://github.com/spoqa/geofront-cli/pull/18


Version 0.4.2
`````````````

Released on February 26, 2020.

- Added supporting for LibreSSL. [`#16`__ by cynthia]

__ https://github.com/spoqa/geofront-cli/pull/16


Version 0.4.1
`````````````

Released on May 24, 2017.

- Fixed a bug that ``geofront-cli go``/``gfg`` had crashed with
  ``AttributeError`` when a user cancelled (i.e. Ctrl-C) to select a remote.
  [`#10`__]

__ https://github.com/spoqa/geofront-cli/issues/10


Version 0.4.0
`````````````

Released on May 23, 2017.

- Dropped support of Python 2.6 and 3.2.
- ``geofront-cli go`` command and its alias shortcut ``gfg`` were introduced.
  It's an interactive user interface to select a remote and SSH to it at once.
- Fixed verification failure of SSL certificates when Python was installed
  using Homebrew on macOS.  Now it depends on Certifi_.
- Now the output list of ``geofront-cli remotes`` is sorted.
- The second column of ``geofront-cli remotes --verbose`` result became
  vertically aligned.
- The second column of ``geofront-cli remotes --verbose`` result became
  to omit the port number if it's 22 so that these are easy to copy-and-paste
  into other SSH programs.
- Loading spinners became shown when time-taking tasks are running.

.. _Certifi: https://github.com/certifi/python-certifi


Version 0.3.4
`````````````

Released on April 3, 2017.

- Fixed ``UnicodeError`` during signing the running Python 3 executable
  on macOS.


Version 0.3.3
`````````````

Released on March 30, 2017.

- Now ``-d``/``--debug`` option prints more debug logs.
- Fixed `system errors during getting/setting password through keyring/Keychain
  on macOS due to some unsigned Python executables`__.

__ https://github.com/jaraco/keyring/issues/219


Version 0.3.2
`````````````

Released on May 31, 2016.

- Fixed ``ImportError`` on Python 2.6.


Version 0.3.1
`````````````

Released on May 28, 2016.

- Forward compatibility with Geofront 0.4.


Version 0.3.0
`````````````

Released on January 15, 2016.

- Fixed an ``AttributeError`` during handling error sent by server.
  [`#4`__]

__ https://github.com/spoqa/geofront-cli/issues/4


Version 0.2.2
`````````````

Released on November 14, 2014.

- Added ``-v``/``--version`` option.
- Fixed an ``AttributeError`` during handling error from server.
  [`#2`__, `#3`__ by Lee Jaeyoung]

__ https://github.com/spoqa/geofront-cli/issues/2
__ https://github.com/spoqa/geofront-cli/pull/3


Version 0.2.1
`````````````

Released on June 29, 2014.

- Added ``geofront-cli scp`` command.
- Added the short option ``-S`` for ``--ssh``.
- It becomes to no more depend on dirspec_.  Instead it's simply bundled
  together.
- ``geofront-cli`` now prints a usage description when no subcommand specified.

.. _dirspec: https://pypi.python.org/pypi/dirspec


Version 0.2.0
`````````````

Released on May 3, 2014.

- Added handling of unfinished authentication error.
- Added handling of incompatible protocol version.


Version 0.1.1
`````````````

Released on April 22, 2014.

- Fixed Python 2 incompatibility.
- Added warning for non-SSL server URL.


Version 0.1.0
`````````````

First pre-alpha release.  Released on April 21, 2014.
