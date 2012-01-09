.. index:: command line interface

==================
Command line usage
==================

This chapter describes how to use cutplace from the command line. It assumes
the user already opened a console window (for example ``Terminal.app`` on Mac
OS X, ``term`` on Linux or ``cmd.exe`` on Windows) and is ready to enter
commands in it.

.. index:: pair: command line option; --help
.. index:: pair: command line option; --listencodings
.. index:: pair: command line option; --version

Show help and other information
===============================

To read a short description of all options available for cutplace, run::

  cutplace --help

To find out which characters encodings cutplace supports, run::

  cutplace --listencodings

To learn which version of cutplace you are using, run::

  cutplace --version

Note that this also prints the version of Python used and a few details on the
platform running on. This is particular useful in case you intend to report
bugs as described in :doc:`support`.

Validate an ICD
===============

To validate that an ICD is syntactically and semantically correct, simply run
cutplace with only the path of the ICD as option. For example, an ICD stored in
CSV format and named ``customer_icd.csv`` can be validated by running::

  cutplace customer_icd.ods

Possible errors show up in the console and result in an exit code of 1.

In case the ICD is in good shape, no error messages appear and the exit code is
0.

ICDs containing non ASCII characters
====================================

If the ICD is provided in CSV format and contains non ASCII characters such as
Umlauts or Kanji, you have to specify the encoding using ``--icd-encoding``::

  cutplace --icd-encoding iso-8859-15 kunden.csv

To obtain a list of all encodings available to cutplace, run::

  cutplace --list-encodings

You can avoid this by storing ICDs in ODS or Excel format, which include
information about the encoding used inside the file already.

Validate that a data file conforms to an ICD
============================================

To validate that a data file conforms to an ICD, pass the path of the ICD and
the data file. For example using the same ICD as in the previous section to
validate a data file containing customers stored in `customers.csv`, run::

  cutplace customer_icd.csv customers.csv

To validate several data files against the same ICD, simply pass them all. For
example::

  cutplace customer_icd.csv customers_east.csv customers_north.csv customers_south.csv customers_west.csv

In case the data do not conform to the ICD, error messages show up in the
console.

.. index:: pair: command line option; --plugins

Import plugsins
===============

You can define your own field format and checks in simple Pyhton modules and
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
  existent data files, insufficient file access rights or broken ICD's.

* Errors in the data format that prevent it from validating the whole file. For
  example, the ICD might specify a line separator "LF" (linefeed) but the data
  file uses "CRLF" (carriage return and linefeed). In such a case, cutplace
  will stop the validation once it encounters the wrong separator.

* Errors in the data that violate the rules specified in the ICD for fields and
  checks. For example, the ICD might specify that a field is an integer number
  but the data file contains letters in it.  In such a case, cutplace will
  report the specific line and column of the field, and continue with the next
  one.

TODO: elaborate

.. index:: pair: command line option; --split

If ``--split`` is set, cutplace stores each row in one of two files:

#. A CSV file containing the rows that have been accepted. It uses a comma (,)
   as separator and UTF-8 as character encoding. This file can be helpful in case
   you decide to process the valid part of the data even if some of them where
   broken.

#. A text file containing a raw dump of each rejected row and the related error
   message. It uses UTF-8 as character encoding and Python's `repr()` format to
   render the data. This has the advantage that hairy issues such as control
   characters or padding white space are easy to see.

These files are stored in the same folder as the data file and have a the same
name but a suffix of "_accepted.csv" and "_rejected.txt" appended.

.. index:: pair: command line option; --trace

The command line option ``--trace`` can be helpful for tracking down bugs in
the rules you specified for complex checks like ``DistinctCount``, field
formats or checks you developed yourself, or in cutplace itself. When enabled,
error messages related to issues in the data include a Python stack trace,
which might contain information useful to developers.

.. index:: web interface
.. index:: pair: command line option; --web
.. index:: pair: command line option; --port

Launching the web server
========================

In addition to the command line interface cutplace offers a graphical user
interface accessible for web browsers. It does so by launching a little web
server that offers a simple page where you can select the files containing the
ICD and data. Simply run::

  cutplace --web

This should result in the following output::

  INFO:cutplace.server:cutplace
  INFO:cutplace.server:Visit http://localhost:8778/ to connect
  INFO:cutplace.server:Press Control-C to shut down

Next open your browser and point it to the address shown in the output. Then
select the ICD and data file to validate and click ``Validate``. The resulting
pages shows the data, where green rows indicate proper data and red rows point
out broken data.

In case you want to run the server at a different port than 8778, specify the
``--port`` option, for example::

  cutplace --web --port 1234

Note that this is a very simple web server, and it will not support hundreds of
users attempting to access it at the same time.

Also be aware that everyone can access it unless your firewall restricts access
to it.
