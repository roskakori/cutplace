===========
Development
===========

Cutplace is open source software, so its source code is available for you to
inspect, extend and play around with. This chapter describes where to get it,
how to build it and how to contribute to the project.

If you are just interested to use cutplace's library classes and functions,
refer to the chapter about the :doc:`api`.


Obtaining additional tools and Python packages
==============================================

To build the source code, you need a few additional tools and Python packages.

First there are a couple of Python packages:

* coverage
* epydoc
* nose
* profiler
* sphinx

The easiest way to install them is running::

  easy_install coverage epydoc nose profiler sphinx

If you are using Ubuntu, you should instead use ``apt-get``::

  sudo apt-get install python-setuptools
  sudo apt-get install python-profiler
  sudo easy_install coverage epydoc nose sphinx

.. index:: epydoc

Sadly, epydoc 3.0.1 does not work with docutils 0.6, so in case you are using
a reasonably modern Python version, it will fail with::

  'Text' object has no attribute 'data'

In order to fix this, open ``epydoc/markup/restructuredtext.py``, locate
``_SummaryExtractor.visit_paragraph()`` and change the lines below marked
with ``# FIXED`` comments::

  for child in node:
     if isinstance(child, docutils.nodes.Text):
         # FIXED: m = self._SUMMARY_RE.match(child.data)
         text = child.astext()
         m = self._SUMMARY_RE.match(text)
         if m:
             summary_pieces.append(docutils.nodes.Text(m.group(1)))
             # FIXED: other = child.data[m.end():]
             other = text[m.end():]
             if other and not other.isspace():
                 self.other_docs = True
             break
     summary_pieces.append(child)

And finally you might need `ant <http://ant.apache.org/>`_,  a build tool popular in the Java world.
Although most of the build process is covered by ``setup.py`` and a some custom
Python modules, a few things use ant. The reason for that is partially because
it is more robust and portable than using shell scripts for the same thing
and partially because it seems easier to write and maintain an ant target
than adding a new ``setup.py`` command. Ideally though there would be no need for
ant and everything would be covered by ``setup.py``.

.. index:: repository, source code

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
