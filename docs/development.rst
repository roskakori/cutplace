===========
Development
===========

Cutplace is open source software, so its source code is available for you to
inspect, extend and play around with. This chapter describes where to get it,
how to build it and how to contribute to the project.

If you are interested in using cutplace's classes and functions, refer to the
chapter about the :doc:`api`.

.. index:: build, poetry

Obtain and build the source code
================================

The source code for cutplace is available via a Git repository from
https://github.com/roskakori/cutplace. Visit http://help.github.com/ to
learn how to browse, download or fork the source code.

To build the source code, you need a few additional tools and Python packages.

First, you need to install
`poetry <https://python-poetry.org/docs/#installation>`_.

Then you can run the test cases. When run for the first time, this also
installs all the dependencies, which might take a while::

  $ poetry run pytest

To build the distribution archives::

  $ poetry build

The :file:`scripts` folder contains a few shell scripts to build other parts:

* :file:`build_documentation.sh`: Build the Sphinx documentation.
* :file:`build_performance_test_report.sh`: Build a performance test report.
* :file:`build_test_coverage_report.sh`: Build a test coverage report for
  manual browsing. View file:`htmlcov/index.html` to take a look at it.
* :file:`update_dependencies.sh`: Update dependencies to the most current
  version.

.. index:: repository, source code


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


Source code contributions
=========================

In case you fixed any bugs or added improvements to cutplace, feel free to
contribute your changes by forking the repository and issuing a pull request
as described at http://help.github.com/fork-a-repo/.


Developer cheat sheet
=====================

This section makes it easier for developers to remember how to perform
certain common but rarely necessary tasks.

Update the version number in :file:`pyproject.toml`::

  [tool.poetry]
  name = "cutplace"
  version = "0.9.x"

Build the distribution archives::

  $ poetry build

Tag a release (simply replace ``0.9.x`` with the current version number)::

  $ git tag -a -m "Tagged version 0.9.x." v0.9.x
  $ git push --tags

Upload release to PyPI::

  $ poetry run pytest
  $ poetry publish
