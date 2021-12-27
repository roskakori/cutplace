"""
Input and output of data rows in various formats validating only the basic
format but not any :py:mod:`cutplace.fields` or :py:mod:`cutplace.checks`.
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
import csv
import datetime
import io
import os
import zipfile
from contextlib import closing
from xml.etree import ElementTree

import xlrd
import xlsxwriter

from cutplace import _compat, _tools, data, errors

# Valid line delimiters for  `fixed_rows()`.
_VALID_FIXED_ANY_LINE_DELIMITERS = ("\n", "\r", "\r\n")
_VALID_FIXED_LINE_DELIMITERS = data.LINE_DELIMITER_TO_TEXT_MAP.keys()

# Namespaces used by OpenOffice.org documents.
_OOO_NAMESPACES = {
    "chart": "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dom": "http://www.w3.org/2001/xml-events",
    "dr3d": "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "field": "urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "form": "urn:oasis:names:tc:opendocument:xmlns:form:1.0",
    "math": "http://www.w3.org/1998/Math/MathML",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "number": "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    "of": "urn:oasis:names:tc:opendocument:xmlns:of:1.2",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "ooo": "http://openoffice.org/2004/office",
    "oooc": "http://openoffice.org/2004/calc",
    "ooow": "http://openoffice.org/2004/writer",
    "presentation": "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0",
    "rdfa": "http://docs.oasis-open.org/opendocument/meta/rdfa#",
    "rpt": "http://openoffice.org/2005/report",
    "script": "urn:oasis:names:tc:opendocument:xmlns:script:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "xforms": "http://www.w3.org/2002/xforms",
    "xlink": "http://www.w3.org/1999/xlink",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
_NUMBER_COLUMNS_REPEATED = "{" + _OOO_NAMESPACES["table"] + "}number-columns-repeated"


def _excel_cell_value(cell, datemode):
    """
    The value of ``cell`` as text taking into account the way excel encodes
    dates and times.

    Numeric Excel types (Currency,  Fractional, Number, Percent, Scientific)
    simply return the decimal number without any special formatting.

    Dates result in a text using the format "YYYY-MM-DD", times in a text
    using the format "hh:mm:ss".

    Boolean results in "0" or "1".

    Formulas are evaluated and return the respective result.

    :param str datemode: the datemode from the workbook the cell was read \
      from; refer to the :py:mod:`xlrd` documentation for more details
    """
    assert cell is not None

    if cell.ctype == xlrd.XL_CELL_DATE:
        cell_tuple = xlrd.xldate_as_tuple(cell.value, datemode)
        assert len(cell_tuple) == 6, "cell_tuple=%r" % cell_tuple
        if cell_tuple[:3] == (0, 0, 0):
            time_tuple = cell_tuple[3:]
            result = str(datetime.time(*time_tuple))
        else:
            result = str(datetime.datetime(*cell_tuple))
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        default_error_text = xlrd.error_text_from_code[0x2A]  # same as "#N/A!"
        error_code = cell.value
        result = str(xlrd.error_text_from_code.get(error_code, default_error_text))
    elif isinstance(cell.value, str):
        result = cell.value
    else:
        result = str(cell.value)
        if (cell.ctype == xlrd.XL_CELL_NUMBER) and (result.endswith(".0")):
            result = result[:-2]

    return result


def excel_rows(source_path, sheet=1):
    """
    Rows read from an Excel document (both :file:`*.xls` and :file:`*.xlsx`
    thanks to :py:mod:`xlrd`).

    :param str source_path: path to the Excel file to be read
    :param int sheet: the sheet in the file to be read
    :return: sequence of lists with each list representing a row in the \
      Excel file
    :raises cutplace.errors.DataFormatError: in case the file cannot be read
    """
    assert source_path is not None
    assert sheet >= 1, "sheet=%r" % sheet

    location = errors.Location(source_path, has_cell=True)
    try:
        with xlrd.open_workbook(source_path) as book:
            sheet = book.sheet_by_index(0)
            datemode = book.datemode
            for y in range(sheet.nrows):
                row = []
                for x in range(sheet.ncols):
                    row.append(_excel_cell_value(sheet.cell(y, x), datemode))
                    location.advance_cell()
                yield row
                location.advance_line()
    except xlrd.XLRDError as error:
        raise errors.DataFormatError("cannot read Excel file: %s" % error, location)
    except UnicodeError as error:
        raise errors.DataFormatError("cannot decode Excel data: %s" % error, location)


def _raise_delimited_data_format_error(delimited_path, reader, error):
    location = errors.Location(delimited_path)
    line_number = reader.line_num
    if line_number > 0:
        location.advance_line(line_number)
    raise errors.DataFormatError("cannot parse delimited file: %s" % error, location)


def _as_delimited_keywords(delimited_data_format):
    assert delimited_data_format is not None
    assert delimited_data_format.is_valid
    assert delimited_data_format.format == data.FORMAT_DELIMITED

    if delimited_data_format.escape_character == delimited_data_format.quote_character:
        doublequote = True
        escapechar = None
    else:
        doublequote = False
        escapechar = delimited_data_format.escape_character
    result = {
        "delimiter": delimited_data_format.item_delimiter,
        "doublequote": doublequote,
        "escapechar": escapechar,
        "quotechar": delimited_data_format.quote_character,
        "quoting": delimited_data_format.quoting,
        "skipinitialspace": delimited_data_format.skip_initial_space,
        "strict": True,
    }
    return result


def delimited_rows(delimited_source, data_format):
    """
    Rows in ``delimited_source`` with using ``data_format``. In case
    ``data_source`` is a string, it is considered a path to file which
    is automatically opened and closed in oder to retrieve the data.
    Otherwise ``data_source`` is assumed to be a filelike object that
    can be read directly and is be opened and closed by the caller.

    :raises cutplace.errors.DataFormatError: if ``delimited`` source is not
      a valid delimited file
    """
    if isinstance(delimited_source, str):
        delimited_stream = io.open(delimited_source, "r", newline="", encoding=data_format.encoding)
        has_opened_delimited_stream = True
    else:
        delimited_stream = delimited_source
        has_opened_delimited_stream = False
    keywords = _as_delimited_keywords(data_format)
    try:
        delimited_reader = _compat.csv_reader(delimited_stream, **keywords)
        try:
            for row in delimited_reader:
                yield row
        except (csv.Error, UnicodeDecodeError) as error:
            _raise_delimited_data_format_error(delimited_source, delimited_reader, error)
    finally:
        if has_opened_delimited_stream:
            delimited_stream.close()


def _findall(element, xpath, namespaces):
    # TODO: Cleanup: Replace calls to this function by direct calls to element.findall().
    result = element.findall(xpath, namespaces)
    return result


def ods_rows(source_ods_path, sheet=1):
    """
    Rows stored in ODS document ``source_ods_path`` in ``sheet``.

    :raises cutplace.errors.DataFormarError: if ``source_ods_path`` is not \
      a valid ODS file.
    """
    assert sheet >= 1

    def ods_content_root():
        """
        `ElementTree` for content.xml in `source_ods_path`.
        """
        assert source_ods_path is not None

        location = errors.Location(source_ods_path)
        try:
            # HACK: Use ``closing()`` because of Python 2.6.
            with closing(zipfile.ZipFile(source_ods_path, "r")) as zip_archive:
                try:
                    xml_data = zip_archive.read("content.xml")
                except Exception as error:
                    raise errors.DataFormatError("cannot extract content.xml for ODS spreadsheet: %s" % error, location)
        except errors.DataFormatError:
            raise
        except Exception as error:
            raise errors.DataFormatError("cannot uncompress ODS spreadsheet: %s" % error, location)

        with io.BytesIO(xml_data) as xml_stream:
            try:
                tree = ElementTree.parse(xml_stream)
            except Exception as error:
                raise errors.DataFormatError("cannot parse content.xml: %s" % error, location)

        return tree.getroot()

    content_root = ods_content_root()
    table_elements = list(
        _findall(content_root, "office:body/office:spreadsheet/table:table", namespaces=_OOO_NAMESPACES)
    )
    table_count = len(table_elements)
    if table_count < sheet:
        error_message = "ODS must contain at least %d sheet(s) instead of just %d" % (sheet, table_count)
        raise errors.DataFormatError(error_message, errors.Location(source_ods_path))
    table_element = table_elements[sheet - 1]
    location = errors.Location(source_ods_path, has_cell=True, has_sheet=True)
    for _ in range(sheet - 1):
        location.advance_sheet()
    for table_row in _findall(table_element, "table:table-row", namespaces=_OOO_NAMESPACES):
        row = []
        for table_cell in _findall(table_row, "table:table-cell", namespaces=_OOO_NAMESPACES):
            repeated_text = table_cell.attrib.get(_NUMBER_COLUMNS_REPEATED, "1")
            try:
                repeated_count = int(repeated_text)
                if repeated_count < 1:
                    raise errors.DataFormatError(
                        "table:number-columns-repeated is %s but must be at least 1" % _compat.text_repr(repeated_text),
                        location,
                    )
            except ValueError:
                raise errors.DataFormatError(
                    "table:number-columns-repeated is %s but must be an integer" % _compat.text_repr(repeated_text),
                    location,
                )
            text_p = table_cell.find("text:p", namespaces=_OOO_NAMESPACES)
            if text_p is None:
                cell_value = ""
            else:
                cell_value = text_p.text
            row.extend([cell_value] * repeated_count)
            location.advance_cell(repeated_count)
        yield row
        location.advance_line()


def fixed_rows(fixed_source, encoding, field_name_and_lengths, line_delimiter="any"):
    r"""
    Rows found in file ``fixed_source`` using ``encoding``. The name and
    (fixed) length of the fields for each row are specified as a list of
    tuples ``(name, length)``. Each row can end with a line feed unless
    ``line_delimiter`` equals ``None``. Valid values are: ``'\n'``, ``'\r'``
    and ``'\r\n'``, in which case other values result in a
    `errors.DataFormatError`. Additionally ``'any'`` accepts any of the
    previous values.
    """
    assert fixed_source is not None
    assert encoding is not None
    for name, length in field_name_and_lengths:
        assert name is not None
        assert length >= 1, "length for %s must be at least 1 but is %s" % (name, length)
    assert line_delimiter in _VALID_FIXED_LINE_DELIMITERS, "line_delimiter=%s but must be one of: %s" % (
        _compat.text_repr(line_delimiter),
        _VALID_FIXED_LINE_DELIMITERS,
    )

    # Predefine variable for access in local function.
    location = errors.Location(fixed_source, has_column=True)
    fixed_file = None
    # HACK: list with at most 1 character to be unread after a line feed. We
    # need to use a list so `_has_data_after_skipped_line_delimiter` can
    # modify its contents.
    unread_character_after_line_delimiter = [None]

    def _has_data_after_skipped_line_delimiter():
        """
        If `fixed_file` has data, assume they are a line delimiter as specified
        by `line_delimiter` and read and validate them.

        In case `line_delimiter` is `None`, the result is always ``True`` even
        if the input has already reached its end.
        """
        assert location is not None
        assert line_delimiter in _VALID_FIXED_LINE_DELIMITERS
        assert unread_character_after_line_delimiter[0] is None

        result = True
        if line_delimiter is not None:
            if line_delimiter == "\r\n":
                actual_line_delimiter = fixed_file.read(2)
            else:
                assert line_delimiter in ("\n", "\r", "any")
                actual_line_delimiter = fixed_file.read(1)
            if actual_line_delimiter == "":
                result = False
            elif line_delimiter == "any":
                if actual_line_delimiter == "\r":
                    # Process the optional '\n' for 'any'.
                    anticipated_linefeed = fixed_file.read(1)
                    if anticipated_linefeed == "\n":
                        actual_line_delimiter += anticipated_linefeed
                    elif anticipated_linefeed == "":
                        result = False
                    else:
                        # Unread the previous character because it is unrelated to line delimiters.
                        unread_character_after_line_delimiter[0] = anticipated_linefeed
                if actual_line_delimiter not in _VALID_FIXED_ANY_LINE_DELIMITERS:
                    valid_line_delimiters = _tools.human_readable_list(_VALID_FIXED_ANY_LINE_DELIMITERS)
                    raise errors.DataFormatError(
                        "line delimiter is %s but must be one of: %s"
                        % (_compat.text_repr(actual_line_delimiter), valid_line_delimiters),
                        location,
                    )
            elif actual_line_delimiter != line_delimiter:
                raise errors.DataFormatError(
                    "line delimiter is %s but must be %s"
                    % (_compat.text_repr(actual_line_delimiter), _compat.text_repr(line_delimiter)),
                    location,
                )
        return result

    if isinstance(fixed_source, str):
        fixed_file = io.open(fixed_source, "r", encoding=encoding)
        is_opened = True
    else:
        fixed_file = fixed_source
        is_opened = False

    has_data = True
    try:
        while has_data:
            field_index = 0
            row = []
            for field_name, field_length in field_name_and_lengths:
                if unread_character_after_line_delimiter[0] is None:
                    item = fixed_file.read(field_length)
                else:
                    assert len(unread_character_after_line_delimiter) == 1
                    item = unread_character_after_line_delimiter[0]
                    if field_length >= 2:
                        item += fixed_file.read(field_length - 1)
                    unread_character_after_line_delimiter[0] = None
                assert unread_character_after_line_delimiter[0] is None
                if not is_opened:
                    # Ensure that the input is a text file, `io.StringIO` or something similar. Binary files,
                    # `io.BytesIO` and the like cannot be used because the return bytes instead of strings.
                    # NOTE: We do not need to use _compat.text_repr(item) because type `unicode` does not fail here.
                    assert isinstance(item, str), "%s: fixed_source must yield strings but got type %s, value %r" % (
                        location,
                        type(item),
                        item,
                    )
                item_length = len(item)
                if item_length == 0:
                    if field_index > 0:
                        names = [name for name, _ in field_name_and_lengths]
                        lengths = [length for _, length in field_name_and_lengths]
                        previous_field_index = field_index - 1
                        characters_needed_count = sum(lengths[field_index:])
                        list_of_missing_field_names = _tools.human_readable_list(names[field_index:], "and")
                        raise errors.DataFormatError(
                            "after field '%s' %d characters must follow for: %s"
                            % (names[previous_field_index], characters_needed_count, list_of_missing_field_names),
                            location,
                        )
                    # End of input reached.
                    has_data = False
                elif item_length == field_length:
                    row.append(item)
                    location.advance_column(field_length)
                    field_index += 1
                else:
                    raise errors.DataFormatError(
                        "cannot read field '%s': need %d characters but found only %d: %s"
                        % (field_name, field_length, item_length, _compat.text_repr(item)),
                        location,
                    )
            if has_data and not _has_data_after_skipped_line_delimiter():
                has_data = False
            if len(row) > 0:
                yield row
                location.advance_line()
    finally:
        if is_opened:
            fixed_file.close()


def auto_rows(source):
    """
    Determine basic data format of `source` based on heuristics and return its contents.
    If source is a string, it is considered a path to a file, otherwise assume it is a
    text stream providing a ``read()`` method.
    """
    result = None
    if isinstance(source, str):
        suffix = os.path.splitext(source)[1].lstrip(".").lower()
        if suffix == "ods":
            result = ods_rows(source)
        elif suffix in ("xls", "xlsx"):
            result = excel_rows(source)
    elif isinstance(source, io.BytesIO):
        # TODO: Assume ODS; cannot use XLS and XLSX (at least not without temp file) because the readers need a file.
        raise NotImplementedError("ODS from io.BytesIO")
    if result is None:
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        # TODO: Use chardet to figure out an encoding.
        delimited_format.set_property(data.KEY_ENCODING, "utf-8")
        # TODO: Determine delimiter by counting common delimiters
        #  with the first 4096 bytes and choosing the maximum one.
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, ",")
        delimited_format.validate()
        result = delimited_rows(source, delimited_format)

    return result


class AbstractRowWriter(object):
    """
    Base class for writers that can write rows to ``target`` using a certain
    :py:class:`~cutplace.data.DataFormat`.

    :param target: :py:class:`str` or filelike object to write to; a \
      :py:class:`str` is assumed to be a path to a file which is \
      automatically opened during in the constructor and closed with \
      :py:meth:`~.cutplace.rowio.AbstractRowWriter.close` or by using the \
      ``with`` statement
    :param cutplace.data.DataFormat: data format to use for writing
    """

    def __init__(self, target, data_format):
        assert target is not None
        assert data_format is not None
        assert data_format.is_valid

        self._data_format = data_format
        self._has_opened_target_stream = False
        if isinstance(target, str):
            self._target_path = target
            self._target_stream = io.open(self._target_path, "w", encoding=data_format.encoding, newline="")
            self._has_opened_target_stream = True
        else:
            try:
                self._target_path = target.name
            except AttributeError:
                self._target_path = "<io>"
            self._target_stream = target
        self._location = errors.Location(self.target_path, has_cell=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._has_opened_target_stream:
            assert self.target_stream is not None
            self.close()

    @property
    def data_format(self):
        return self._data_format

    @property
    def location(self):
        """
        The :py:class:`cutplace.errors.Location` to write the next row to.
        This is automatically advanced by
        :py:meth:`~.cutplace.rowio.AbstractRowWriter.write_row`.
        """
        return self._location

    @property
    def target_path(self):
        return self._target_path

    @property
    def target_stream(self):
        return self._target_stream

    def write_row(self, rows_to_write):
        raise NotImplementedError

    def write_rows(self, rows_to_write):
        assert self.target_stream is not None
        assert rows_to_write is not None

        for row_to_write in rows_to_write:
            self.write_row(row_to_write)

    def close(self):
        if self._has_opened_target_stream:
            self._target_stream.close()
            self._has_opened_target_stream = False
        self._target_stream = None
        self._target_path = None


class DelimitedRowWriter(AbstractRowWriter):
    def __init__(self, target, data_format):
        assert target is not None
        assert data_format is not None
        assert data_format.format == data.FORMAT_DELIMITED
        assert data_format.is_valid

        super().__init__(target, data_format)
        keywords = _as_delimited_keywords(data_format)
        self._delimited_writer = _compat.csv_writer(self._target_stream, **keywords)

    def write_row(self, row_to_write):
        try:
            self._delimited_writer.writerow(row_to_write)
        except UnicodeEncodeError as error:
            raise errors.DataFormatError("cannot write data row: %s; row=%s" % (error, row_to_write), self.location)
        self._location.advance_line()


class FixedRowWriter(AbstractRowWriter):
    def __init__(self, target, data_format, field_names_and_lengths):
        assert target is not None
        assert data_format is not None
        assert data_format.format == data.FORMAT_FIXED
        assert data_format.is_valid
        assert field_names_and_lengths is not None
        for field_name, field_length in field_names_and_lengths:
            assert field_name is not None
            assert field_length is not None
            assert field_length >= 1, "field_length=%r" % field_length

        super().__init__(target, data_format)
        self._field_names_and_lengths = field_names_and_lengths
        self._expected_row_item_count = len(self._field_names_and_lengths)
        if self.data_format.line_delimiter == "any":
            self._line_separator = os.linesep
        else:
            self._line_separator = self.data_format.line_delimiter

    def write_row(self, row_to_write):
        """
        Write a row of fixed length strings.

        :param list row_to_write: a list of str where each item must have \
          exactly the same length as the corresponding entry in \
          :py:attr:`~.field_lengths`
        :raises AssertionError: if ``row_to_write`` is not a list of \
          strings with each matching the corresponding ``field_lengths`` \
          as specified to :py:meth:`~.__init__`.
        """
        assert row_to_write is not None
        row_to_write_item_count = len(row_to_write)
        assert (
            row_to_write_item_count == self._expected_row_item_count
        ), "%s: row must have %d items instead of %d: %s" % (
            self.location,
            self._expected_row_item_count,
            row_to_write_item_count,
            row_to_write,
        )
        if __debug__:
            for field_index, field_value in enumerate(row_to_write):
                self.location.set_cell(field_index)
                field_name, expected_field_length = self._field_names_and_lengths[field_index]
                assert isinstance(field_value, str), "%s: field %s must be of type %s instead of %s: %r" % (
                    self.location,
                    _compat.text_repr(field_name),
                    str.__name__,
                    type(field_value).__name__,
                    field_value,
                )
                actual_field_length = len(field_value)
                assert (
                    actual_field_length == expected_field_length
                ), "%s: field %s must have exactly %d characters instead of %d: %r" % (
                    self.location,
                    _compat.text_repr(field_name),
                    expected_field_length,
                    actual_field_length,
                    field_value,
                )
            self.location.set_cell(0)

        try:
            self._target_stream.write("".join(row_to_write))
        except UnicodeEncodeError as error:
            raise errors.DataFormatError("cannot write data row: %s; row=%s" % (error, row_to_write), self.location)
        if self._line_separator is not None:
            self._target_stream.write(self._line_separator)
        self.location.advance_line()


class XlsxRowWriter(AbstractRowWriter):
    """
    A writer for Excel 2007+ (:file:`*.xlsx`) documents.

    Additionally, to the common interface provided by
    :py:class:`~.AbstractRowWriter` the internal :py:attr:`~.workbook` and
    :py:attr:`~.worksheet` can be accessed and modified before calling
    :py:meth:`cutplace.rowio.XlsxRowWriter.close` in order to add for
    instance formatting or charts using the operations provided by
    :py:class:`xlsxwriter.XlsxWriter`.
    """

    def __init__(self, target_path):
        """
        Set up a writer that stores the data in ``target_path``, which has to
        be a string. Unlike with some other writers, this can not be stream.

        Internally data are written to a worksheet first and written to a
        file during :py:meth:`cutplace.rowio.XlsxRowWriter.close`.
        """
        assert target_path is not None
        assert isinstance(target_path, str), "target_path must be a string but is: %s" % type(target_path)

        self._target_path = target_path
        self._target_stream = None
        self._has_opened_target_stream = False
        self._location = errors.Location(self.target_path, has_cell=True)
        self._workbook = xlsxwriter.Workbook(self.target_path)
        self._worksheet = self._workbook.add_worksheet()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def workbook(self):
        """
        The Excel workbook with the :py:attr:`~.worksheet` the written data
        are stored in.

        After :py:meth:`cutplace.rowio.XlsxWriter.close` this is ``None``.
        """
        return self._workbook

    @property
    def worksheet(self):
        """
        The sole Excel worksheet the written data are stored in.

        After :py:meth:`cutplace.rowio.XlsxWriter.close` this is ``None``.

        :rtype: xlsxwriter.Worksheet
        """
        return self._worksheet

    def write_row(self, row_to_write):
        assert row_to_write is not None

        row_index = self.location.line
        for item in row_to_write:
            assert item is not None
            assert not isinstance(item, bytes), "item must be a string: %r" % item
            column_index = self.location.cell
            if isinstance(item, str):
                # Write strings as explicit strings to prevent strings starting with '=' from being converted to
                # formulas.
                self.worksheet.write_string(row_index, column_index, item)
            else:
                self.worksheet.write(row_index, column_index, item)
            self.location.advance_cell()
        self.location.advance_line()

    def close(self):
        """
        Close :py:attr:`~.workbook` and physically write it to
        :py:attr:`~cutplace.rowio.XlsxWriter.target_path`.
        """
        if self.workbook is not None:
            self.workbook.close()
            self._workbook = None
            self._worksheet = None
            self._target_path = None
