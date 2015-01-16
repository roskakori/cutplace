"""
Cutplace is a tool to validate that tabular data stored in CSV, Excel, ODS
and PRN files conform to an interface definition (CID).

Additionally to the command line tool the functionality of cutplace is also
accessible through a Python API.
"""
from cutplace.data import DataFormat, FORMAT_DELIMITED, FORMAT_EXCEL, FORMAT_FIXED, FORMAT_ODS
from cutplace.errors import \
    CheckError, CutplaceError, DataError, DataFormatError, FieldValueError, InterfaceError, Location, RangeValueError
from cutplace.interface import Cid
from cutplace.ranges import Range
from cutplace.validio import Reader
from cutplace._version import get_versions

#: Package version information.
__version__ = get_versions()['version']
del get_versions

#: Public classes and functions.
__all__ = [
    'Cid',
    'CheckError',
    'CutplaceError',
    'DataError',
    'DataFormat',
    'DataFormatError',
    'FORMAT_DELIMITED',
    'FORMAT_EXCEL',
    'FORMAT_FIXED',
    'FORMAT_ODS',
    'FieldValueError',
    'InterfaceError',
    'Location',
    'Range',
    'RangeValueError',
    'Reader',
    '__version__'
]
