=======================================
Cutplace
=======================================

Cutplace is a tool and API to validate that tabular and flat data conform
to an interface definition (CID). Cutplace checks CSV, PRN (fixed
length), Excel and ODS files using configurable separators, delimiters and
fillers. It supports error conditions for single cells, across rows or
concerning the whole set of data.

CID's are simple spread sheets that describe the basic file format of the
data to validate, the fields provided and additional conditions to check
across rows or the whole data set.

Additionally cutplace offers an API to validate and read data described
by a CID. It provides a uniform interface to :py:class:`csv.reader` and
packages to read other formats, saving you from having to learn the
intrinsics of each package.

* `Download cutplace from PyPI <http://pypi.python.org/pypi/cutplace/>`_
  or run ``easy_install cutplace``.

* :doc:`Read the tutorial <tutorial>` to find out what cutplace can do for
  you and how it works.

* Read the :doc:`application programmer interface tutorial <api>` to learn how
  to integrate cutplace based validations in your own application. For a
  complete reference, browse the
  `API reference documentation <http://roskakori.github.com/cutplace/api/>`_.

* Take a look at the
  `roadmap <https://github.com/roskakori/cutplace/issues/milestones>`_ to
  find out what the future has in store.

* Read the :doc:`developer guide <development>` to learn how to obtain the
  source code, build a distribution archive and contribute patches.

To find out more, take a look at the :doc:`table of contents <contents>` or
visit the `project site <https://github.com/roskakori/cutplace>`_.

Contents
========

**TODO** Fix contents

.. toctree::
   :maxdepth: 2

   License <license>
   Module Reference <_rst/modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
