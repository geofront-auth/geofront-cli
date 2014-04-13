Geofront CLI client
===================

It provides a CLI client for Geofront_, a simple SSH key management server.

.. _Geofront: https://geofront.readthedocs.org/


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
