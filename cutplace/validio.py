"""
Validated input and output of tabular data in various formats.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
import itertools

from cutplace import _compat, data, errors, interface, rowio

# Valid choices for ``on_error`` parameter.
_VALID_ON_ERROR_CHOICES = ("continue", "raise", "yield")


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

    def __init__(self, cid_or_path):
        assert cid_or_path is not None

        if isinstance(cid_or_path, str):
            self._cid = interface.Cid(cid_or_path)
        else:
            self._cid = cid_or_path
            assert (
                self._cid.data_format.is_valid
            ), "DataFormat.validate() must be called before using a CID for validation"
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

    def validate_row(self, row):
        """
        Validate a single ``row``:

        1. Check if the number of items in ``row`` matches the number of
           fields in the CID
        2. Check that all fields conform to their field format (as defined
           by :py:class:`cutplace.fields.AbstractFieldFormat` and its
           descendants)
        3. Check that the row conforms to all row checks (as defined by
           :py:meth:`cutplace.checks.AbstractCheck.check_row`)

        The caller is responsible for :py:attr:`~.location` pointing to the
        correct row in the data while ``validate_row`` takes care of calling
        :py:meth:`cutplace.errors.Location.set_cell` appropriately.
        """
        assert row is not None
        assert self.location is not None

        # Validate that number of fields.
        actual_item_count = len(row)
        if actual_item_count < self._expected_item_count:
            raise errors.DataError(
                "row must contain %d fields but only has %d: %s" % (self._expected_item_count, actual_item_count, row),
                self.location,
            )
        if actual_item_count > self._expected_item_count:
            raise errors.DataError(
                "row must contain %d fields but has %d, additional values are: %s"
                % (self._expected_item_count, actual_item_count, row[self._expected_item_count :]),
                self.location,
            )

        # Validate each field according to its format.
        for field_index, field_value in enumerate(row):
            self.location.set_cell(field_index)
            field_to_validate = self.cid.field_formats[field_index]
            try:
                if not isinstance(field_value, str):
                    raise errors.FieldValueError(
                        "type must be %s instead of %s: %s"
                        % (str.__name__, type(field_value).__name__, _compat.text_repr(field_value))
                    )
                field_to_validate.validated(field_value)
            except errors.FieldValueError as error:
                error.prepend_message(
                    "cannot accept field %s" % _compat.text_repr(field_to_validate.field_name), self.location
                )
                raise

        # Validate the whole row according to row checks.
        self.location.set_cell(0)
        field_map = _create_field_map(self.cid.field_names, row)
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
    def __init__(self, cid_or_path, source_data_stream_or_path, on_error="raise", validate_until=None):
        """
        An iterator that produces possibly validated rows from
        ``source_data_stream_or_path`` conforming to ``cid_or_path``.

        If a row cannot be read, ``on_error`` specifies what to do about it:

        * ``'continue'``: quietly continue with the next row.
        * ``'raise'`` (the default): raise an exception and stop reading.
        * ``'yield'``: instead of of a row, the result contains a \
          :py:exc:`cutplace.errors.DataError`.

        :param validate_until: number of rows after which validation should \
          stop; further rows are still produces but not validated anymore; \
          ``None`` all rows should be validated (the default); 0 means no \
          rows should be validated
        :type: int or None
        """
        assert cid_or_path is not None
        assert source_data_stream_or_path is not None
        assert on_error in _VALID_ON_ERROR_CHOICES, "on_error=%r" % on_error
        assert (validate_until is None) or (validate_until >= 0)

        super().__init__(cid_or_path)
        # TODO: Consolidate obtaining source path with other code segments that do similar things.
        if isinstance(source_data_stream_or_path, str):
            source_path = source_data_stream_or_path
        else:
            try:
                source_path = source_data_stream_or_path.name
            except AttributeError:
                source_path = "<io>"
        self._location = errors.Location(source_path, has_cell=True)
        self._source_data_stream_or_path = source_data_stream_or_path
        self._on_error = on_error
        self._validate_until = validate_until
        self.accepted_rows_count = None
        self.rejected_rows_count = None

    @property
    def on_error(self):
        return self._on_error

    def _raw_rows(self):
        data_format = self.cid.data_format
        format = data_format.format
        if format == data.FORMAT_EXCEL:
            return rowio.excel_rows(self._source_data_stream_or_path, data_format.sheet)
        elif format == data.FORMAT_DELIMITED:
            return rowio.delimited_rows(self._source_data_stream_or_path, data_format)
        elif format == data.FORMAT_FIXED:
            return rowio.fixed_rows(
                self._source_data_stream_or_path,
                data_format.encoding,
                interface.field_names_and_lengths(self.cid),
                data_format.line_delimiter,
            )
        elif format == data.FORMAT_ODS:
            return rowio.ods_rows(self._source_data_stream_or_path, data_format.sheet)
        else:
            assert False, "format=%r" % format

    def rows(self):
        """
        Data rows of ``source_path``.

        Even with ``on_error`` set to ' continue'  or 'yield' certain errors
        still cause a stop, for example checks at the end of the file still
        raise a :py:exc:`cutplace.errors.CheckError` and generally broken
        files result in a
        :py:exc:`cutplace.errors.DataFormatError`.

        :raises cutplace.errors.DataError: on broken data
        """
        self.accepted_rows_count = 0
        self.rejected_rows_count = 0
        for check in self.cid.check_map.values():
            check.reset()
        header_row_count = self._cid.data_format.header
        for row_count, row in enumerate(self._raw_rows(), 1):
            try:
                is_after_header_row = row_count > header_row_count
                is_before_validate_until = (self._validate_until is None) or (row_count <= self._validate_until)
                if is_after_header_row:
                    if is_before_validate_until:
                        self.validate_row(row)
                    self.accepted_rows_count += 1
                    yield row
            except errors.DataError as error:
                if self.on_error == "raise":
                    raise
                self.rejected_rows_count += 1
                if self.on_error == "yield":
                    yield error
                else:
                    assert self.on_error == "continue"
            self._location.advance_line()

    def validate_rows(self):
        """
        Validate that the data read from
        :py:meth:`~cutplace.validio.Reader.rows()` conform to
        :py:attr:`~cutplace.validio.Reader.cid`.

        In order to check everything, :py:meth:`~.Reader.close()` has to be
        called to also validate the checks at the end of the data.

        :raises cutplace.errors.DataError: on broken data
        """
        for _ in self.rows():
            pass


class Writer(BaseValidator):
    def __init__(self, cid_or_path, target):
        assert cid_or_path is not None
        assert target is not None

        super().__init__(cid_or_path)

        data_format = cid_or_path.data_format
        assert self.cid.data_format.is_valid
        self._header = data_format.header
        self._delegated_writer = None
        if data_format.format == data.FORMAT_DELIMITED:
            self._delegated_writer = rowio.DelimitedRowWriter(target, data_format)
        elif data_format.format == data.FORMAT_FIXED:
            self._field_names_and_lengths = interface.field_names_and_lengths(self.cid)
            self._delegated_writer = rowio.FixedRowWriter(target, data_format, self._field_names_and_lengths)
        else:
            raise NotImplementedError("data_format=%r" % data_format.format)

    @property
    def location(self):
        """
        The location in the :py:class:`cutplace.rowio.AbstractRowWriter` used
        to actually write the data.
        """
        return self._delegated_writer.location if self._delegated_writer is not None else None

    def _padded_fixed_row(self, row):
        """
        Same as ``row`` but with items possibly padded with trailing blanks in order to fix fixed length.
        """
        assert row is not None
        assert len(row) == len(self.cid.field_formats)
        result = []
        for field_index, field_value in enumerate(row):
            field_value_length = len(field_value)
            _, fixed_field_length = self._field_names_and_lengths[field_index]
            if field_value_length < fixed_field_length:
                field_value += " " * (fixed_field_length - field_value_length)
            result.append(field_value)
        return result

    def write_row(self, row_to_write):
        assert row_to_write is not None
        assert self._delegated_writer is not None

        if self.location.line >= self._header:
            self.validate_row(row_to_write)
        if self.cid.data_format.format == data.FORMAT_FIXED:
            actual_row_to_write = self._padded_fixed_row(row_to_write)
        else:
            actual_row_to_write = row_to_write
        self._delegated_writer.write_row(actual_row_to_write)

    def write_rows(self, rows_to_write):
        assert rows_to_write is not None

        for row_to_write in rows_to_write:
            self.write_row(row_to_write)

    def close(self):
        try:
            super().close()
        finally:
            if self._delegated_writer is not None:
                self._delegated_writer.close()
                self._delegated_writer = None


def rows(cid_or_path, data_stream_or_path, on_error="raise", validate_until=None):
    """
    Rows read from ``data`` and validated against ``cid_or_path``.

    :param cid_or_path: :py:class:`cutplace.Cid` or :py:class:`str` \
      describing a path pointing to a CID
    :param data_stream_or_path: filelike object or :py:class:`str` \
      describing a path pointing to the data to be read
    :param str on_error: same as ``on_error`` for :py:class:`cutplace.Reader`
    :param validate_until: same as ``validate_until`` for \
      :py:class:`cutplace.Reader`
    :raises cutplace.errors.DataError: on broken data but only in case \
      ``on_error='raise'`` (the default)
    :raises cutplace.errors.InterfaceError: on a broken CID
    """
    assert cid_or_path is not None
    assert data_stream_or_path is not None
    assert on_error in _VALID_ON_ERROR_CHOICES, "on_error=%r" % on_error
    assert (validate_until is None) or (validate_until >= 0)

    with Reader(cid_or_path, data_stream_or_path, on_error, validate_until) as reader:
        for row in reader.rows():
            yield row


def validate(cid_or_path, data_stream_or_path, validate_until=None):
    """
    Validate that ``data_or_path`` conform to ``cid_or_path``.

    :param cid_or_path: :py:class:`cutplace.Cid` or :py:class:`str` \
      describing a path pointing to a CID
    :param data_stream_or_path: filelike object or :py:class:`str` \
      describing a path pointing to the data to be read
    :raises cutplace.errors.DataError: on broken data
    :raises cutplace.errors.InterfaceError: on a broken CID
    """
    assert cid_or_path is not None
    assert data_stream_or_path is not None
    assert (validate_until is None) or (validate_until >= 0)

    with Reader(cid_or_path, data_stream_or_path, validate_until=validate_until) as reader:
        rows_to_validate = reader.rows()
        if validate_until is not None:
            rows_to_validate = itertools.islice(rows_to_validate, validate_until)
        for _ in rows_to_validate:
            pass
