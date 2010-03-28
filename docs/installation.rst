=========================
Download and Installation
=========================

This chapter describes how to install the cutplace command line application and
what you need to run it.

Requirements
============

In order to run cutplace you need Python 2.5 or later, available from
http://www.python.org/ for many platforms. To check if Python is already
installed, run::

  python --version

In case Python is installed, you should see an output like the following (the
version number may vary)::

  Python 2.5.4

Other than that, there are no special software requirements for cutplace.
Hardware wise, any reasonably modern computer should easily meet the demands of
cutplace. Memory usage depends on the amount of data you process, 256 MB of
memory should be more than enough even for large datasets.

Download and install using PyPI and easy_install
================================================

Cutplace can be downloaded from http://pypi.python.org/pypi, the Python Package
Index.

If you have `easy_install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ installed, simply run::

  easy_install cutplace

to download and install the most current version. If you later on want to
upgrade to a new version, run::

  easy_install --upgrade cutplace

Alternatively you can manually download and install cutplace by visiting
http://pypi.python.org/pypi/cutplace/.

When this is finished, run::

  cutplace --help

to get a short overview of the available command line options (they are
explained in detail in :doc:`command-line-usage`).

Download and install using PyPI with Mac OS X and MacPorts
==========================================================

MacPorts provide a command-line driven software package under a BSD License,
and through it easy access to thousands of ports that greatly simplify the task
of compiling and installing open-source software on your Mac. To find out more
about MacPorts, visit http://www.macports.org/.

``Easy_install`` is included with ``setuptools``, which are already available
as MacPorts package. So in order to install them, simply run::

  sudo port install py25-setuptools

For Python 2.6, use::

  sudo port install py26-setuptools

After that you can proceed as describe above and run::

  easy_install-2.5 cutplace

respectively::

  easy_install-2.6 cutplace

Download and install using the Subversion repository
====================================================

In case you prefer to install cutplace directly from the source, you can use
its subversion repository as described in :doc:`development`.

Download and run using Jython
=============================

Jython is an implementation of Python written in 100% Pure Java, and seamlessly
integrated with the Java platform. It thus allows you to run Python on any Java
platform. To find out more, visit http://www.jython.org/.

You need Jython 2.5 which at the time of this writing does not integrate with
``setuptools``, so you need to use the Subversion repository and then run it
using something like::

  jython .../path/to/cutplace/cutplace/cutplace.py --help

This should output the quick help.
