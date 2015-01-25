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

from cutplace import data
from cutplace import errors
from cutplace import interface
from cutplace import rowio


def _create_field_map(field_names, field_values):
    assert field_names
    assert field_values
    assert len(field_names) == len(field_values)

    return dict(zip(field_names, field_values))


class BaseValidator(object):
    """
    A general validator to validate a single row (by validating its fields
    and perform row checks), perform final checks when done with all rows
    and finally release all resources required to do that.

    The :py:attr:`~.location` has to be set by descendants. While
    :py:meth:`~.validate_row` takes care of advancing the cell, descendants
    are responsible for advancing the row (by calling
    :py:meth:`cutplace.errors.Location.advance_line`).

    It also provides a context manager and can consequently be used with the
    ``with`` statement.
    """
    def __init__(self, cid):
        assert cid is not None

        self._cid = cid
        self._expected_item_count = len(self._cid.field_formats)
        self._location = None
        self._is_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Simply call :py:meth:`~.close()`.
        """
        self.close()

    @property
    def cid(self):
        """
        The CID to validate the data.

        :rtype: cutplace.interface.Cid
        """
        return self._cid

    @property
    def location(self):
        """
        The current location in the data to validate.

        :rtype: cutplace.errors.Location
        """
        return self._location

    def validate_row(self, field_values):
        """
        Validate ``row`` by:

        1. Check if the number of items in ``row`` matches the number of
           fields in the CID
        2. Check that all fields conform to their field format (as defined
           by :py:class:`cutplace.fields.AbstractFieldFormat` and its
           descendants)
        3. Check that the row conforms to all row checks (as defined by
           :py:meth:`cutplace.checks.AbstractCheck.check_row`)

        The caller is responsible for :py:attr:`~.location` pointing to the
        correct row in the data while ``validate_row`` take care of calling
        :py:meth:`~.Location.advance_cell` appropriately.
        """
        assert field_values is not None
        assert self.location is not None

        # Validate that number of fields.
        actual_item_count = len(field_values)
        if actual_item_count < self._expected_item_count:
            raise errors.DataError(
                'row must contain %d fields but only has %d: %s'
                % (self._expected_item_count, actual_item_count, field_values),
                self._location)
        if actual_item_count > self._expected_item_count:
            raise errors.DataError(
                'row must contain %d fields but has %d, additional values are: %s'
                % (self._expected_item_count, actual_item_count, field_values[self._expected_item_count:]),
                self.location)

        # Validate each field according to its format.
        for field_index, field_value in enumerate(field_values):
            field_to_validate = self.cid.field_formats[field_index]
            try:
                field_to_validate.validated(field_value)
            except errors.FieldValueError as error:
                error.prepend_message('cannot accept field %s' % field_to_validate.field_name, self.location)
                raise
            self.location.advance_cell()

        # Validate the whole row according to row checks.
        field_map = _create_field_map(self.cid.field_names, field_values)
        for check_name in self.cid.check_names:
            self.cid.check_map[check_name].check_row(field_map, self.location)

    def close(self):
        """
        Validate final checks and release all resources. When called a second
        time, do nothing.

        :raises cutplace.errors.CheckError: if any \
          :py:meth:`cutplace.checks.AbstractCheck.check_at_end` fails.
        """
        if not self._is_closed:
            try:
                for check_name in self.cid.check_names:
                    self.cid.check_map[check_name].check_at_end(self.location)
            finally:
                for check in self.cid.check_map.values():
                    check.cleanup()
            self._is_closed = True


class Reader(BaseValidator):
    def __init__(self, cid, source_path):
        assert cid is not None
        assert source_path is not None

        super(Reader, self).__init__(cid)
        self._source_path = source_path
        self.accepted_rows_count = None
        self.rejected_rows_count = None

    def _raw_rows(self):
        data_format = self.cid.data_format
        if data_format.format == data.FORMAT_EXCEL:
            return rowio.excel_rows(self._source_path, data_format.sheet)
        elif data_format.format == data.FORMAT_DELIMITED:
            return rowio.delimited_rows(self._source_path, data_format)
        elif data_format.format == data.FORMAT_FIXED:
            return rowio.fixed_rows(
                self._source_path, data_format.encoding, interface.field_names_and_lengths(self.cid),
                data_format.line_delimiter)
        elif data_format.format == data.FORMAT_ODS:
            return rowio.ods_rows(self._source_path, data_format.sheet)

    @property
    def source_path(self):
        """
        The path of the dat file to be read.
        """
        return self._source_path

    def rows(self, on_error='raise'):
        """
        Data rows of ``source_path``.

        If a row cannot be read, ``on_error`` specifies what to do about it:

        * ``'continue'``: quietly continue with the next row.
        * ``'raise'`` (the default): raise an exception and stop reading.
        * ``'yield'``: instead of of a row, the result contains a :py:exc:`cutplace.errors.DataError`.

        Even with ``on_error`` set to ' continue'  or 'yield' certain errors
        still cause a stop, for example checks at the end of the file still
        raise a :py:exc:`cutplace.errors.CheckError` and generally broken
        files result in a
        :py:exc:`cutplace.errors.DataFormatError`.

        :raises cutplace.errors.DataError: on broken data
        """
        assert on_error in ('continue', 'raise', 'yield')

        self._location = errors.Location(self._source_path, has_cell=True)
        self.accepted_rows_count = 0
        self.rejected_rows_count = 0
        for check in self.cid.check_map.values():
            check.reset()
        for row in self._raw_rows():
            try:
                self.validate_row(row)
                self.accepted_rows_count += 1
                yield row
            except errors.DataError as error:
                if on_error == 'raise':
                    raise
                self.rejected_rows_count += 1
                if on_error == 'yield':
                    yield error
                else:
                    assert on_error == 'continue'
            self._location.advance_line()

    def validate_rows(self):
        """
        Validate that the data read from
        :py:meth:`~cutplace.validio.Reader.rows()` conform to
        :py:attr:`~cutplace.validio.Reader.cid`.

        In order to check everything, :py:meth`~.close()` has to be
        called to also validate the checks at the end of the data.

        :raises cutplace.errors.DataError: on broken data
        """
        for _ in self.rows():
            pass


class Writer(BaseValidator):
    def __init__(self, cid, target):
        assert cid is not None
        assert target is not None
        data_format = cid.data_format
        assert data_format.is_valid

        super(Writer, self).__init__(cid)
        self._delegated_writer = None
        if data_format.format == data.FORMAT_DELIMITED:
            self._delegated_writer = rowio.DelimitedRowWriter(target, data_format)
        elif data_format.format == data.FORMAT_FIXED:
            field_lengths = interface.field_lengths(cid)
            self._delegated_writer = rowio.FixedRowWriter(target, data_format, field_lengths)
        else:
            raise NotImplementedError('data_format=%r' % data_format.format)

    @property
    def location(self):
        """
        The location in the :py:class:`cutplace.rowio.AbstractRowWriter` used
        to actually write the data.
        """
        return self._delegated_writer.location if self._delegated_writer is not None else None

    def write_row(self, row_to_write):
        assert row_to_write is not None
        assert self._delegated_writer is not None

        self.validate_row(row_to_write)
        self._delegated_writer.write_row(row_to_write)

    def write_rows(self, rows_to_write):
        assert rows_to_write is not None
        assert self._delegated_writer is not None

        for row_to_write in rows_to_write:
            self._delegated_writer.write_row(row_to_write)

    def close(self):
        try:
            super(Writer, self).close()
        finally:
            if self._delegated_writer is not None:
                self._delegated_writer.close()
                self._delegated_writer = None
