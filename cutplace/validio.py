"""
Validated input and output of tabular data in various formats.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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
from cutplace import interface
from cutplace import rowio


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
        self.accepted_rows_count = None
        self.rejected_rows_count = None

    def _raw_rows(self):
        data_format = self._cid.data_format
        if data_format.format == data.FORMAT_EXCEL:
            return rowio.excel_rows(self._source_path, data_format.sheet)
        elif data_format.format == data.FORMAT_DELIMITED:
            return rowio.delimited_rows(self._source_path, data_format)
        elif data_format.format == data.FORMAT_FIXED:
            return rowio.fixed_rows(
                self._source_path, data_format.encoding, interface.field_names_and_lengths(self._cid),
                data_format.line_delimiter)
        elif data_format.format == data.FORMAT_ODS:
            return rowio.ods_rows(self._source_path, data_format.sheet)

    @property
    def source_path(self):
        """
        The path of the file to be read.
        """
        return self._source_path

    def rows(self, on_error='raise'):
        """
        Data rows of `source_path`.

        If a row cannot be read, ``on_error`` specified what to do about it:

        * 'continue': quietly continue with the next row
        * 'raise' (the default): raise an exception and stop reading.
        * 'yield': instead of of a row, the result contains an `errors.DataError`

        Even with ``on_error`` set to ' continue'  or 'yield' certain errors still cause a stop, for example checks
        at the end of the file still raise a `errors.CheckError` and generally broken files result in an
        `error.DataFormatError`.
        """
        assert on_error in ('continue', 'raise', 'yield')

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
                field_to_validate = self._cid.field_formats[i]
                try:
                    field_to_validate.validated(field_values[i])
                except errors.FieldValueError as error:
                    field_name = field_to_validate.field_name
                    error.prepend_message('cannot accept field %s' % field_name, self._location)
                    raise
                self._location.advance_cell()

        def validate_row_checks(field_values):
            field_map = _create_field_map(self._cid.field_names, field_values)
            for check_name in self._cid.check_names:
                self._cid.check_map[check_name].check_row(field_map, self._location)

        def validate_checks_at_end():
            for check_name in self._cid.check_names:
                self._cid.check_map[check_name].check_at_end(self._location)

        self.accepted_rows_count = 0
        self.rejected_rows_count = 0
        for check in self._cid.check_map.values():
            check.reset()
        try:
            for row in self._raw_rows():
                try:
                    validate_field_formats(row)
                    validate_row_checks(row)
                    self.accepted_rows_count += 1
                    yield row
                    self._location.advance_line()
                except errors.DataError as error:
                    if on_error == 'raise':
                        raise
                    self.rejected_rows_count += 1
                    if on_error == 'yield':
                        yield error
                    else:
                        assert on_error == 'continue'
            validate_checks_at_end()
        finally:
            for check in self._cid.check_map.values():
                check.cleanup()

    def validate(self):
        for _ in self.rows():
            pass

    def close(self):
        pass
