============
Installation
============

This chapter describes how to install the cutplace command line application and
what you need to run it.

Requirements
============

In order to run cutplace you need Python 3.3 respectively Python 2.6 or any
later version, available from http://www.python.org/ for many platforms. To
check if Python is already installed, run::

  python --version

In case Python is installed, you should see an output like the following (the
actual version number may vary)::

  Python3.4.2

Additionally you the ``pip`` package installer. Newer versions of Python
already include it. Otherwise it is available from
https://pypi.python.org/pypi/pip/.

Download and Installation
=========================

To install the latest version of ``cutplace`` simply run::

  pip install --upgrade cutplace

You can also manually download the package from
http://pypi.python.org/pypi/cutplace/.

When this is finished, run::

  cutplace --help

to get a short overview of the available command line options (they are
explained in detail in :doc:`command-line-usage`).
