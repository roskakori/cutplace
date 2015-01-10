.. index:: command line interface

==================
Command line usage
==================

This chapter describes how to use cutplace from the command line. It assumes
the user already opened a console window (for example ``Terminal.app`` on Mac
OS X, ``term`` on Linux or ``cmd.exe`` on Windows) and is ready to enter
commands in it.

.. index:: pair: command line option; --help
.. index:: pair: command line option; --version


Show help and other information
===============================

To read a short description of all options available for cutplace, run::

  cutplace --help

To learn which version of cutplace you are using, run::

  cutplace --version

Note that this also prints the version of Python used and a few details on the
platform running on. This is particular useful in case you intend to report
bugs as described in :doc:`support`.


Validate a CID
==============

To validate that a CID is syntactically and semantically correct, simply run
cutplace with the path of the CID as only option. For example, an CID stored in
ODS format and named ``cid_customers.ods`` can be validated by running::

  cutplace cid_customers.ods

Possible errors show up in the console and result in an exit code of 1.

In case the CID is in good shape, no error messages appear and the exit code is
0.


Validate that a data file conforms to an CID
============================================

To validate that a data file conforms to an CID, pass the path of the CID and
the data file. For example using the same CID as in the previous section to
validate a data file containing customers stored in ``cid_customers.ods``,
run::

  cutplace cid_customers.ods customers_data.csv

To validate several data files against the same CID, simply pass them all. For
example::

  cutplace cid_customers.csv customers_north_data.csv customers_south_data.csv

In case the data do not conform to the CID, error messages show up in the
console.


.. index:: pair: command line option; --plugins

Import plugsins
===============

You can define your own field format and checks in simple Python modules and
tell cutplace to import them. For more information on how to write such
modules see :ref:`using-own-check-and-field-formats`.

To import all plugins located in the folder ``~/cutplace-plugins``, use::

  cutplace --plugins ~/cutplace-plugins ...

This will import and initialize all ``*.py`` files in this folder. To see
which checks and field formats are actually recognized, also specify
``--log=info``.


Dealing with errors
===================

Roughly speaking cutplace can encounter the following kinds of errors when
validating data:

* Errors that prevent cutplace from validating the data at all, such as non
  existent data files, insufficient file access rights or broken CID's.

* Errors in the data format that prevent it from validating the whole file. For
  example, the CID might specify a line separator "LF" (linefeed) but the data
  file uses "CRLF" (carriage return and linefeed). In such a case, cutplace
  will stop the validation once it encounters the wrong separator.

* Errors in the data that violate the rules specified in the CID for fields and
  checks. For example, the CID might specify that a field is an integer number
  but the data file contains letters in it.  In such a case, cutplace will
  report the specific line and column of the field, and continue with the next
  one.

**TODO**: elaborate on dealing with errors, in particular exit code
