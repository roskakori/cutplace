"""
Cutplace is a tool to validate that tabular data stored in CSV, Excel, ODS
and PRN files conform to an interface definition (CID).

Additionally to the command line tool the functionality of cutplace is also
accessible through a Python API.

Module overview
---------------

* :py:mod:`~cutplace.checks` - standard checks for rows and whole data sets
* :py:mod:`~cutplace.data` - data formats to describe the basic structure of a data set
* :py:mod:`~cutplace.errors` - all errors raised by cutplace
* :py:mod:`~cutplace.fields` - standard field formats and an abstract field format tha can easily be extended
* :py:mod:`~cutplace.interface` - everything need to describe a data set
* :py:mod:`~cutplace.iotools` - basic input and output of tabular data without low level validation
* :py:mod:`~cutplace.ranges` - basic classes to describe ranges of values
* :py:mod:`~cutplace.validator` - high level reading and validation tabular data
"""
from cutplace._version import get_versions

#: Package version information.
__version__ = get_versions()['version']
del get_versions
