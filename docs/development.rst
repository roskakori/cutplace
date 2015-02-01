===========
Development
===========

Cutplace is open source software, so its source code is available for you to
inspect, extend and play around with. This chapter describes where to get it,
how to build it and how to contribute to the project.

If you are interested in using cutplace's classes and functions, refer to the
chapter about the :doc:`api` and the :ref:`modindex`.


Obtain additional tools and Python packages
===========================================

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

Using ant in a Python project might seem unusual, but there are good
reasons for that:

* ant is more robust and portable than using shell scripts for the same
  thing.

* It is easier to write and maintain an ant target than adding a new
  :file:`setup.py` command. This is particularly true for targets that just
  call a few command line tools and move around a couple of files.

.. index:: repository, source code


Obtain and build the source code
================================

The source code for cutplace is available via a Git repository from
https://github.com/roskakori/cutplace. Visit http://help.github.com/ to
learn how to browse, download or fork the source code.


Project overview
----------------

The source code consists of:

* :file:`build.xml` is the project file for the build tool `ant
  <http://ant.apache.org/>`_

* :file:`cutplace/*.py` are the Python modules for cutplace

* :file:`tests/test_*.py` are test cases for unittest

* :file:`tests/data/*` are test data used by the unittests; some of them
  are :file:`*.ods`, :file:`*.xls` or :file:`*.xlsx` spread sheet you can
  edit using Calc from `OpenOffice.org <http://www.openoffice.org/>`_.

* :file:`docs/*` is the reStructuredText for the user guide

* :file:`examples/*` contains the example date used in the :doc:`tutorial`
  and code examples on how to use the cutplace Python module in you own code.

Common ant targets
------------------

Once you have your local copy of the source code, use :command:`ant` to build
and test cutplace.

To build the source distribution, run::

  $ ant sdist

To build a binary distribution, run::

  $ ant bdist_wheel

To run the test suite::

  $ ant unittest

To also run doctests and test the examples in the documentation::

 $ ant test

To build the documentation::

 $ ant docs

To remove files generated during the build process::

  $ ant clean


Source code contributions
=========================

In case you fixed any bugs or added improvements to cutplace, feel free to
contribute your changes by forking the repository and issuing a pull request
as described at http://help.github.com/fork-a-repo/.


Developer cheat sheet
=====================

This section makes it easier for developers to remember how to perform
certain common but rarely necessary tasks.

To install the current work copy as a developer build, use::

  $ python setup.py develop

Once the related version is published, you can install it using::

  $ pip install --upgrade cutplace

This ensures that the current version found on PyPI is installed even if
a locally installed developer build has the same version.

Run cutplace locally from console::

  $ export PYTHONPATH=`pwd`:`pwd`/cutplace:`pwd`/tests
  $ python -m cutplace.applications --version

Create the installer archive::

  $ python setup.py sdist --formats=zip
  $ python setup.py bdist_wheel

Test that the distribution archive can be installed and run in a fresh
terminal session::

  $ ant sdist
  $ virtualenv-3.4 /tmp/cpt
  $ source /tmp/cpt/bin/activate
  $ pip install ~/workspace/cutplace/dist/cutplace-0.8.x.zip
  $ cutplace --version
  $ cd
  $ rm -rf /tmp/cpt
  $ ^D

Tag a release (simply replace ``0.8.x`` with the current version number)::

  $ git tag -a -m "Tagged version 0.8.x." v0.8.x
  $ git push --tags

Upload release to PyPI::

  $ ant flake8 test docs
  $ python setup.py sdist --formats=zip upload
  $ python setup.py bdist_wheel upload
