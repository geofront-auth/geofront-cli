Geofront CLI client
===================

.. image:: https://badge.fury.io/py/geofront-cli.svg?
   :target: https://pypi.python.org/pypi/geofront-cli
   :alt: Latest PyPI version

.. image:: https://travis-ci.org/spoqa/geofront-cli.svg?
   :target: https://travis-ci.org/spoqa/geofront-cli

It provides a CLI client for Geofront_, a simple SSH key management server.

.. _Geofront: https://geofront.readthedocs.org/


Installation
------------

It is available on PyPI__, so you can install it using ``pip`` installer.

.. code-block:: console

   $ pip install geofront-cli

__ https://pypi.python.org/pypi/geofront-cli


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

- Wrapper around ``scp``
- Shortcut for ``geofront-cli ssh`` command
- Make ``geofront-cli ssh`` similar to ``ssh``
- Autocompletion


Author and license
------------------

`Hong Minhee`__ wrote geofront-cli, and Spoqa_ maintains it.
It is licensed under GPLv3_ or later.

__ http://dahlia.kr/
.. _Spoqa: http://www.spoqa.com/
.. _GPLv3: http://www.gnu.org/licenses/gpl-3.0.html


Changelog
---------

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
