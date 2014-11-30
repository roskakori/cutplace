"""
Validate Data files
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import inspect
import logging
import xlrd

from cutplace import data
from cutplace import cid
from cutplace import fields
from cutplace import errors
from cutplace import checks
from cutplace import _tools

def _create_field_map(field_names, field_values):
    assert field_names
    assert field_values
    assert len(field_names) == len(field_values)

    # FIXME: There must be a more pythonic way to do this.
    result = {}
    for field_index in range(len(field_names) - 1):
        result[field_names[field_index]] = field_values[field_index]
    return result


class Reader(object):
    def __init__(self, cid, source_path):
        self._cid = cid
        self._source_path = source_path
        self._location = None

    def rows(self):
        if self._cid.data_format.format == data.FORMAT_EXCEL:
            return _tools.excel_rows(self._source_path)
        elif self._cid.data_format.format == data.FORMAT_DELIMITED:
            return _tools.delimited_rows(self._source_path, self._cid.data_format)
        elif self._cid.data_format.format == data.FORMAT_FIXED:
            #TODO: implement support for fixed
            pass
        elif self._cid.data_format.format == data.FORMAT_ODS:
            #TODO: implement support for ods
            pass

    def validate(self):
        self._location = errors.InputLocation(self._source_path, has_cell=True)

        for row in self.rows():
            #Validate fields
            if len(row) != len(self._cid.field_formats):
                    raise errors.ValidateLineError('input line is too long or too long/short')
            for i in range(0, len(row)):
                self._cid.field_formats[i].validated(row[i])

            #Validate checks for every row
            field_map = _create_field_map(self._cid.field_names, row)
            for check_name in self._cid.check_names:
                self._cid.check_map[check_name].check_row(field_map, self._location)

            self._location.advance_line()

        #Validate checks at end
        for check_name in self._cid.check_names:
            self._cid.check_map[check_name].check_at_end(self._location)

    def close(self):
        pass
