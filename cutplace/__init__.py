"""
Cutplace is a tool to validate that tabular data stored in CSV, Excel, ODS
and PRN files conform to an interface definition (CID).

Additionally to the command line tool the functionality of cutplace is also
accessible through a Python API.
"""
from cutplace.errors import Location
from cutplace.interface import Cid
from cutplace.ranges import Range
from cutplace.validio import Reader, Writer, validate, rows
from cutplace._version import get_versions

#: Package version information.
__version__ = get_versions()['version']
del get_versions

#: Public classes and functions.
__all__ = [
    'Cid',
    'Location',
    'Range',
    'Reader',
    'Writer',
    'validate',
    'rows',
    '__version__'
]
