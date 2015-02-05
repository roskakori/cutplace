.. index:: command line interface

==================
Command line usage
==================

This chapter describes how to use cutplace from the command line. It assumes
the user already opened a console window (for example :command:`Terminal.app`
on Mac OS X, :command:`term` on Linux or :command:`cmd.exe` on Windows) and
is ready to enter commands in it.

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
cutplace with the path of the CID as only option. For example, a CID stored in
ODS format and named :file:`cid_customers.ods` can be validated by running::

  cutplace cid_customers.ods

Possible errors show up in the console and result in an exit code of 1.

In case the CID is in good shape, no error messages appear and the exit code is
0.


.. index:: pair: command line option; --until

Validate that a data file conforms to a CID
============================================

To validate that a data file conforms to a CID, pass the path of the CID and
the data file. For example using the same CID as in the previous section to
validate a data file containing customers stored in
:file:`cid_customers.ods`, run::

  cutplace cid_customers.ods customers_data.csv

To validate several data files against the same CID, simply pass them all. For
example::

  cutplace cid_customers.csv customers_north_data.csv customers_south_data.csv

In case the data do not conform to the CID, error messages show up in the
console.

To just quickly check that the first few rows of a data file conform the CID,
use the :option:`--until` option. For example::

  cutplace --until 20 cid_customers.ods customers_data.csv

This validates only the first 20 rows in a file, so possible errors in row 21
or later are not detected any more. This is can be useful in production
environments where having to wait for a full validation can be an issue. You
can still do a full validation during testing, so :option:`--until` offers
a trade off between performance and correctness.

Setting :option:`--until=-1` enables validation for all rows (which is the
default) while :option:`--until=0` disables it for the whole file.


.. index:: plugins
.. index:: pair: command line option; --plugins
.. _import-plugins:

Import plugins
==============

You can define your own field format and checks in simple Python modules and
tell cutplace to import them. For more information on how to write such
modules see :ref:`using-own-check-and-field-formats`.

To import all plugins located in the folder :file:`~/cutplace-plugins`, use::

  cutplace --plugins ~/cutplace-plugins ...

This will import and initialize all :file:`*.py` files in this folder. To see
which checks and field formats are actually recognized, also specify
:option:`--log=info`.


.. index:: exit code
.. _exit-code:

Dealing with errors
===================

When :command:`cutplace` detects any errors in the CID or data or cannot
validate them due external circumstances the logs an error messages and sets
an exit code other than 0.

The value of the exist code hints at what needs to be fixed:

* 1 - the syntax of the CID needs fixing or the data must be modified in
  order to conform to the CID

* 2 - the command line options must be fixed

* 3 - a proper environment must be provided for :command:`cutplace` to do its
  tasks. For example, the files containing the CID and data must actually
  exist and be accessible.

* 4 - cutplace (or one of the plugins provided to it) did not expect a
  certain error condition and must be fixed. Unlike previous exit codes,
  these errors also include a Python stack trace pointing to the relevant
  locations in the source code. If you did not provide any plugins (as
  described in :ref:`import-plugins`) or you are certain that the error
  is unrelated to one of your own plugins, file a bug report as described
  in :doc:`support`.
