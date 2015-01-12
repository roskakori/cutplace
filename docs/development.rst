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

To install the Python packages, simply run::

  $ pip install -r requirements-dev.txt

Once these packages are installed, you should be able to build the
distribution archive using::

  $ python setup.py sdist

.. index:: ant

For everything else related to the build, use
`ant <http://ant.apache.org/>`_, a build tool popular in the Java world.
To get an overview of the available ant targets, run::

  $ ant -projecthelp

To build for example the source distribution, run::

  $ ant sdist

Using ant in a Python project might seem unusual, but there are good
reasons for that:

* ant is more robust and portable than using shell scripts for the same
  thing.

* It seems easier to write and maintain an ant target than adding a new
  ``setup.py`` command.

* ant is easy to use for continuous integration driven by Jenkins as
  described in :ref:`jenkins`.

.. index:: sloccount

To monitor the source code size in Jenkins, you need ``sloccount``
available from http://www.dwheeler.com/sloccount/. For Linux, your
distribution most likely has a binary package. For Mac OS X, use the
package provided by Mac Ports.

.. index:: repository, source code

Obtaining and building the source code
======================================

The source code for cutplace is available via a Git repository from
https://github.com/roskakori/cutplace.

The source code consists of:

* :file:`build.xml` is the project file for the build tool `ant
  <http://ant.apache.org/>`_

* :file:`cutplace/*.py` are the Python modules for cutplace

* :file:`tests/test_*.py` are test cases for unittest

* :file:`tests/data/*` are test data used by the unittests; some of them
  are :file:`*.ods` or :file:`*.xls` spread sheet you can edit using
  `OpenOffice.org <http://www.openoffice.org/>`_'s calc

* :file:`docs/*` is the reStructuredText for the web site and user guide

* file:`examples/*` contains the example date used in the :doc:`tutorial` and
  code examples on how to use the cutplace Python module in you own code.

To obtain the source code from the repository you need a Git client. Visit
http://help.github.com/ to learn how to browse or fork the source code.

Once you have your local copy of the source code, use ant to build and test
cutplace.

To just build a binary distribution, run::

  $ ant bdist_wheel

To run all test cases::

  $ ant test

To remove files generated during the build process::

  $ ant clean


Contributing source code
========================

In case you fixed any bugs or added improvements to cutplace, feel free to
contribute your changes by forking the repository and issuing a pull request
as described at http://help.github.com/fork-a-repo/.

Developer notes
===============

This section collects a few final notes interesting for developers.

Install a developer build
-------------------------

To install the current work copy as a developer build, use::

  $ python setup.py develop

Once the related version is published, you can install it using::

  $ pip install --upgrade cutplace

This ensures that the current version found on PyPI is installed even if
a locally installed developer build has the same version.

Add a release tag
-----------------

When publishing a new release, a tag should be added to the repository. This
can be done using the following template::

  $ git tag -a -m "Tagged version 0.8.x." v0.8.x
  $ git push --tags

Simply replace ``0.8.x`` with the current version number.


.. index:: jenkins

.. _jenkins:

Set up Jenkins
--------------

Jenkins is a continuous integration server available from
http://jenkins-ci.org/. It can periodically check for changes committed to
the repository and run then run tests and collect reports.

This section describes how to configure a Jenkins job for cutplace. It
assumes that Jenkins is already installed an running.

First, install the following plugins by navigating to
:menuselection:`Manage Jenkins --> Manage plugins` and then choosing them
from the tab :guilabel:`Available`:

  * Cobertura Plugin
  * Performance Plugin
  * SLOCCount Plug-in
  * Static Code Analysis Plug-ins
  * Task Scanner Plugin
  * Violations plugin

In case Jenkins runs as a deamon on Mac OS X and you are using MacPorts,
navigate to
:menuselection:`Manage Jenkins --> Configure System --> Global Properties`
and add the following environment variables::

  LC_ALL=en_US.UTF-8
  LC_CTYPE=UTF-8
  PATH=/opt/local/bin:/opt/local/sbin:$PATH

Next, create a build using the following steps:

  * Source code management:

    * Git: ``git://github.com/roskakori/cutplace.git``

  * Build triggers:

    * Poll SCM: ``*/10 * * * *``

  * Build:

    #. Invoke ant: targets: ``test site sdist bdist_wheel``

  * Post-build actions:

    #. Scan workspace for open tasks:

       * Files to scan: ``**/*.py, **/*.rst``
       * Files to exclude: ``build/**``
       * Task tags: High=FIXME, normal=TODO, low=HACK

    #. Publish Cobertura Coverage Report: ``**/coverage.xml``
    #. Publish JUnit test result report: ``**/nosetests.xml``
    #. Publish Performance test result report:

       * Choose :menuselection:`Add a new report --> JUnit`
       * :guilabel:`Report files`: ``**/nosetests_performance.xml``

    #. Publish SLOCCount analysis results: SLOCCount reports: ``**/sloccount.sc``
    #. Report Violations: pep8: XML filename pattern: ``**/pep8.txt``
