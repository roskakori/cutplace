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

First there are a couple of Python packages:

* coverage

* profiler

* sphinx

The easiest way to install them is running::

  easy_install coverage profiler sphinx

If you are using Ubuntu, you should instead use ``apt-get``::

  sudo apt-get install python-setuptools
  sudo apt-get install python-profiler
  sudo easy_install coverage sphinx

And finally you might need `ant <http://ant.apache.org/>`_,  a build tool popular in the Java world.
Although most of the build process is covered by ``setup.py`` and a some custom
Python modules, a few things use ant. The reason for that is partially because
it is more robust and portable than using shell scripts for the same thing
and partially because it seems easier to write and maintain an ant target
than adding a new ``setup.py`` command. Ideally though there would be no need for
ant and everything would be covered by ``setup.py``.

Obtaining and building the source code
======================================

The source code for cutplace is available via a Subversion repository from
https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk. You can browse it
at https://apps.sourceforge.net/trac/cutplace/browser/trunk.

The source code consists of:

* ``build.xml`` is the project file for the build tool `ant
  <http://ant.apache.org/>`_

* ``cutplace/*.py`` are the Python modules for cutplace

* ``cutplace/dev_*.py`` are Python modules useful only during
  development

* ``cutplace/test_*.py`` are test cases for unittest

* ``docs/*`` is the reStructuredText for the web site and user guide

* ``examples/*`` contains the example date used in the :doc:`tutorial` and
  code examples on how to use the cutplace Python module in you own code.

* ``tests/*`` contains test data; use for example `OpenOffice.org
  <http://www.openoffice.org/>`_'s calc to edit the ``*.ods`` and ``*.csv``
  files

* ``tests/input/*`` are test data used by the unittest tests in
  ``cutplace/test_*.py``

* ``.project`` and ``.pydevproject`` are for use with `Eclipse
  <http://www.eclipse.org/>`_ and `PyDev <http://pydev.sourceforge.net/>`_.

If Eclipse and PyDev are your developer environment of choice, you can check
out the repository directly from Eclipse using
:menuselection:`File --> New --> Other...` and select
:menuselection:`SVN --> Checkout projects from SVN`.

If you prefer the command line, you need any Subversion client and the build
tool ant.

To check out the current version using the standard Subversion command line
client, run::

  svn checkout https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk cutplace

After the checkout, change to the cutplace folder::

  cd cutplace

To just build a binary distribution, run::

  python setup.py bdist_egg

The output should look something like this::

  running bdist_egg
  running egg_info
  writing requirements to cutplace.egg-info/requires.txt
  writing cutplace.egg-info/PKG-INFO
  ...

To run all test cases::

  python setup.py test

To build the user guide, developer reports and web site::

  ant site

To remove files generated during the build process::

  ant clean

Writing field formats
=====================

Cutplace already ships with several field formats that should cover most needs.
If however you have some very special requirements, you can write your own
formats.

The easiest way to do so is by adding your format to ``cutplace/fields.py``.
Simply inherit from ``AbstractFieldFormat`` and provide a constructor to parse
the ``rule`` parameter. Next, implement ``validatedValue(self, value)`` that
validates that the text in ``value`` conforms to ``rule``. If not, raise an
``FieldValueError`` with a descriptive error message. For examples see any of
the ``*FieldFormat`` classes in ``fields.py``.

The drawback of this approach is that when you install a new version of
cutplace, your changes in ``fields.py`` will be lost.

TODO: Describe how to write a ``myfields.py`` and extend the Python path.

Writing checks
==============

Writing checks is quite similar to writing field formats. The standard checks
are stored in ``cutplace/checks.py``. Inherit from ``AbstractCheck`` and
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

The easiest way to do this is by posting your patch to the
`developer forum <http://apps.sourceforge.net/phpbb/cutplace/viewforum.php?f=4>`_

Developer notes
===============

This section collects a few final notes interesting for developers, especially
for release management.

Add a release tag
-----------------

When publishing a new release, a tag should be added to the repository. This
can be done using the following template::

  svn copy -m "Added tag for version 0.x.x." https://cutplace.svn.sourceforge.net/svnroot/cutplace/trunk https://cutplace.svn.sourceforge.net/svnroot/cutplace/tags/0.x.x

Simply replace ``0.x.x`` with the current version number.
