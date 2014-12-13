"""
Validated processing of data files.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six.moves import zip_longest

from cutplace import data
from cutplace import errors
from cutplace import _io_tools


def _create_field_map(field_names, field_values):
    assert field_names
    assert field_values
    assert len(field_names) == len(field_values)

    return dict(zip_longest(field_names, field_values))


class Reader(object):
    def __init__(self, cid, source_path):
        self._cid = cid
        self._source_path = source_path
        self._location = None

    def _raw_rows(self):
        if self._cid.data_format.format == data.FORMAT_EXCEL:
            return _io_tools.excel_rows(self._source_path, self._cid.data_format.sheet)
        elif self._cid.data_format.format == data.FORMAT_DELIMITED:
            return _io_tools.delimited_rows(self._source_path, self._cid.data_format)
        elif self._cid.data_format.format == data.FORMAT_FIXED:
            # TODO: implement support for fixed.
            pass
        elif self._cid.data_format.format == data.FORMAT_ODS:
            return _io_tools.ods_rows(self._source_path, self._cid.data_format.sheet)

    def rows(self):
        self._location = errors.Location(self._source_path, has_cell=True)
        expected_item_count = len(self._cid.field_formats)

        def validate_field_formats(field_values):
            actual_item_count = len(field_values)
            if actual_item_count < expected_item_count:
                raise errors.DataError(
                    'row must contain %d fields but only has %d: %s' % (expected_item_count, actual_item_count, field_values),
                    self._location)
            if actual_item_count > expected_item_count:
                raise errors.DataError(
                    'row must contain %d fields but has %d, additional values are: %s' % (
                        expected_item_count, actual_item_count, field_values[expected_item_count:]),
                    self._location)
            for i in range(0, actual_item_count):
                self._cid.field_formats[i].validated(field_values[i])
                self._location.advance_cell()

        def validate_row_checks(field_values):
            field_map = _create_field_map(self._cid.field_names, field_values)
            for check_name in self._cid.check_names:
                self._cid.check_map[check_name].check_row(field_map, self._location)

        def validate_checks_at_end():
            for check_name in self._cid.check_names:
                self._cid.check_map[check_name].check_at_end(self._location)

        for row in self._raw_rows():
            validate_field_formats(row)
            validate_row_checks(row)
            yield row
            self._location.advance_line()
        validate_checks_at_end()

    def validate(self):
        for _ in self.rows():
            pass

    def close(self):
        pass
