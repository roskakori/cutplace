===========
Development
===========

Cutplace is open source software, so its source code is available for you to
inspect, extend and play around with. This chapter describes where to get it,
how to change and test the application, how to write your own field formats and
how to contribute to the project.

Obtaining additional tools and Python packages
==============================================

To build the source code, you need a few additional tools and Python packages.

`Ant <http://ant.apache.org/>`_ is a build tool popular in the Java world.
Eventually all the functionality in the build process should be available using
``setup.py``, but for the time being ant is more convenient.

Next there are a couple of Python packages:

* coverage

* profiler

The easiest way to install them is running::

  easy_install coverage profiler

If you are using Ubuntu, you should instead use ``apt-get``::

  sudo apt-get install python-setuptools
  sudo apt-get install python-profiler
  sudo easy_install coverage

Obtaining and building the source code
======================================

The source code for cutplace is available via a Subversion repository from
https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk. You can browse it
at http://cutplace.svn.sourceforge.net/viewvc/cutplace/.

The source code consists of:

* ``build.xml`` is the project file for the build tool `Ant
  <http://ant.apache.org/>`_

* ``version.xml`` contains basic version information

* ``source/cutplace/*.py`` are the Python modules for cutplace

* ``source/cutplace/dev_*.py`` are Python modules useful only during
  development

* ``source/cutplace/test_*.py`` are test cases for unittest

* ``source/site`` is the source code needed to build the cutplace website

* ``source/site/user-guide.xml`` is the Documentation written in `DocBook XML
  <http://www.docbook.org/>`_

* ``source/xml/*.xml`` are XSL transformations for source code generated from
  ``version.xml``

* ``tests/*`` contains test data; use for example `OpenOffice.org
  <http://www.openoffice.org/>`_'s calc to edit the ``*.ods`` and ``*.csv``
  files

* ``tests/input/*`` are test data used by the unittest tests in
  ``source/cutplace/test_*.py``

* ``.project`` and ``.pydevproject`` are for use with `Eclipse
  <http://www.eclipse.org/>`_ and `PyDev <http://pydev.sourceforge.net/>`_.

If Eclipse and PyDev are your developer environment of choice, you can check
out the repository directly from Eclipse using ``File | New | Other...`` and
select ``SVN | Checkout projects from SVN``. After that, you should open
``build.xml`` and run the ant target "setup".

If you prefer the command line, you need any Subversion client and the build
tool ant. Some parts of the code are generated using XSL and ant's ``<xslt>``
task, so simply using distutils alone won't suffice.

To check out the current version using the standard Subversion command line
client, run::

  svn checkout https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk cutplace

After the checkout, change to the cutplace folder and execute the ant target
"setup"::

  cd cutplace
  ant setup

The output should look something like this (replace "..." with your local
project path)::

  Buildfile: build.xml
  setup:
  [untar] Expanding: .../cutplace/external/dtds.tar.bz2 into .../cutplace
  [untar] Expanding: .../cutplace/external/docbook-xsl.tar.bz2 into .../cutplace
  BUILD SUCCESSFUL Total time: 3 seconds

To just build a binary distribution, run::

  ant bdist_egg

The output should look something like this::

  Buildfile: build.xml

    version:
     [xslt] Processing .../cutplace/version.xml to .../cutplace/source/cutplace/version.py
     [xslt] Loading stylesheet .../cutplace/source/xml/version-py.xsl
     [xslt] Processing .../cutplace/version.xml to .../cutplace/setup.py
     [xslt] Loading stylesheet .../cutplace/source/xml/version-setup-py.xsl

    user-guide:
     [xslt] Processing .../cutplace/source/site/user-guide.xml to .../cutplace/site/index.html
     [xslt] Loading stylesheet .../cutplace/docbook-xsl/xhtml/docbook.xsl

    bdist:
     [exec] running bdist
     [exec] running bdist_dumb
     [exec] running build
     [exec] running build_py
     [exec] creating build
     [exec] creating build/lib
     [exec] creating build/lib/cutplace
     [exec] ...

    BUILD SUCCESSFUL

To run all test cases::

  ant test

To build the user guide, developer reports and web site::

  ant site

To remove files generated during the build process::

  ant clean

Writing field formats
=====================

Cutplace already ships with several field formats that should cover most needs.
If however you have some very special requirements, you can write your own
formats.

The easiest way to do so is by adding your format to
``source/cutplace/fields.py``. Simply inherit from ``AbstractFieldFormat`` and
provide a constructor to parse the ``rule`` parameter. Next, implement
``validate(self, item)`` that validates that the text in ``item`` conforms to
``rule``. If not, raise an ``FieldValueError`` with a descriptive error
message. For examples see any of the ``*FieldFormat`` classes in ``fields.py``.

The drawback of this approach is that when you install a new version of
cutplace, your changes in ``fields.py`` will be lost.

TODO: Describe how to write a ``myfields.py`` and extend the Python path.

Writing checks
==============

Writing checks is quite similar to writing field formats. The standard checks
are stored in ``source/cutplace/fields.py``. Inherit from ``AbstractCheck`` and
provide a constructor. You might want to implement at least one of the
following methods:

* ``checkRow(self, rowNumber, row)``: called for each row read from the data.
  ``RowNumber`` is useful to report errors, row is a list where each item
  contains the value from one column as found in the input data.

* ``checkAtEnd(self)``: called when all rows from the data are processed.

In case the check discovers any issues, it should raise a ``CheckError``.

TODO: Describe how to write mychecks.py and extend Python path.

Contributing source code
========================

In case you fixed any bugs or added improvements to cutplace, feel free to
contribute your changes.

The easiest way to do this is by submitting them to the project's patch tracker
at https://sourceforge.net/tracker/?group_id=256054&atid=1126965.

Developer notes
===============

This section collects a few final notes interesting for developers, especially
for release management.

Add a release tag
-----------------

When publishing a new release, a tag should be added to the repository. This
can be done using the following template::

  svn copy -m "Added tag for version 0.x.x." https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk https://cutplace.svn.sourceforge.net/svnroot/cutplace/tags/0.x.x</userinput>

Simply replace ``0.x.x`` with the current version number.
