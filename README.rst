Geofront CLI client
===================

It provides a CLI client for Geofront_, a simple SSH key management server.

.. _Geofront: https://geofront.readthedocs.org/


Installation
------------

It currently isn't available on PyPI, but you can install it using ``pip``
installer.  Though you have to specify ``--allow-external`` and
``--allow-unverified`` options (related issues: 1__, 2__).

.. code-block::

   $ pip install --allow-external dirspec --allow-unverified dirspec -e .

__ http://stackoverflow.com/q/23014238/383405
__ https://bugs.launchpad.net/dirspec/+bug/1298163


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
