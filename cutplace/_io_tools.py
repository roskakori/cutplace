"""
Various internal utility functions.
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
import io
import os
import sys
import six
import csv
import xlrd
import zipfile
from xml.etree import ElementTree
import datetime

from cutplace import errors
from cutplace import _tools

# Valid line delimiters for  `fixed_rows()`.
_VALID_FIXED_ANY_LINE_DELIMITERS = ('\n', '\r', '\r\n')
_VALID_FIXED_LINE_DELIMITERS = _VALID_FIXED_ANY_LINE_DELIMITERS + ('any', None)

# Namespaces used by OpenOffice.org documents.
_OOO_NAMESPACES = {
    'chart': 'urn:oasis:names:tc:opendocument:xmlns:chart:1.0',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dom': 'http://www.w3.org/2001/xml-events',
    'dr3d': 'urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'field': 'urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'form': 'urn:oasis:names:tc:opendocument:xmlns:form:1.0',
    'math': 'http://www.w3.org/1998/Math/MathML',
    'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
    'number': 'urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0',
    'of': 'urn:oasis:names:tc:opendocument:xmlns:of:1.2',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'ooo': 'http://openoffice.org/2004/office',
    'oooc': 'http://openoffice.org/2004/calc',
    'ooow': 'http://openoffice.org/2004/writer',
    'presentation': 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0',
    'rdfa': 'http://docs.oasis-open.org/opendocument/meta/rdfa#',
    'rpt': 'http://openoffice.org/2005/report',
    'script': 'urn:oasis:names:tc:opendocument:xmlns:script:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'xforms': 'http://www.w3.org/2002/xforms',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}
_NUMBER_COLUMNS_REPEATED = '{' + _OOO_NAMESPACES['table'] + '}number-columns-repeated'


def _excel_cell_value(cell, datemode):
    """
    The value of ``cell`` as text taking into account the way excel encodes dates and times.

    Numeric Excel types (Currency,  Fractional, Number, Percent, Scientific) simply yield the decimal number
    without any special formatting.

    Dates result in a text using the format "YYYY-MM-DD", times in a text using the format "hh:mm:ss".

    Boolean yields "0" or "1".

    Formulas are evaluated and yield the respective result.
    """
    assert cell is not None

    if cell.ctype == xlrd.XL_CELL_DATE:
        cellTuple = xlrd.xldate_as_tuple(cell.value, datemode)
        assert len(cellTuple) == 6, "cellTuple=%r" % cellTuple
        if cellTuple[:3] == (0, 0, 0):
            timeTuple = cellTuple[3:]
            result = str(datetime.time(*timeTuple))
        else:
            result = str(datetime.datetime(*cellTuple))
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        defaultErrorText = xlrd.error_text_from_code[0x2a]  # same as "#N/A!"
        errorCode = cell.value
        result = str(xlrd.error_text_from_code.get(errorCode, defaultErrorText), "ascii")
    elif isinstance(cell.value, str):
        result = cell.value
    else:
        result = str(cell.value)
        if (cell.ctype == xlrd.XL_CELL_NUMBER) and (result.endswith(".0")):
            result = result[:-2]

    return result


def excel_rows(source_path, sheet=1):
    assert source_path is not None
    assert sheet >= 1, 'sheet=%r' % sheet

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
        raise errors.DataFormatError('cannot read Excel file: %s' % error, location)
    except UnicodeError as error:
        raise errors.DataFormatError('cannot decode Excel data: %s' % error, location)


def _raise_delimited_data_format_error(delimited_path, reader, error):
    location = errors.Location(delimited_path)
    line_number = reader.line_num
    if line_number > 0:
        location.advance_line(line_number)
    raise errors.DataFormatError('cannot parse delimited file: %s' % error, location)

if sys.version_info[0] >= 3:
    # Read CSV using Python 3.
    def _delimited_rows(delimited_path, encoding, **keywords):
        with io.open(delimited_path, 'r', newline='', encoding=encoding) as delimited_file:
            csv_reader = csv.reader(delimited_file, **keywords)
            try:
                for row in csv_reader:
                    yield row
            except csv.Error as error:
                _raise_delimited_data_format_error(delimited_path, csv_reader, error)

else:  # pragma: no cover
    # Read CSV using Python 2.6+.
    #
    # Note: _UTF8Recoder and _UnicodeReader are derived from <https://docs.python.org/2/library/csv.html#examples>.
    import codecs
    # TODO: Check if the iterators below can be simplified using `six.Iterator` which already has `next()`.

    class _UTF8Recoder(object):
        """
        Iterator that reads an encoded stream and reencodes the input to UTF-8
        """

        def __init__(self, f, encoding):
            self.reader = codecs.getreader(encoding)(f)

        def __iter__(self):
            return self

        def next(self):
            return self.reader.next().encode('utf-8')

    class _UnicodeReader(object):
        """
        A CSV reader which will iterate over lines in the CSV file 'f',
        which is encoded in the given encoding.
        """

        def __init__(self, csv_file, dialect=csv.excel, encoding='utf-8', **keywords):
            csv_file = _UTF8Recoder(csv_file, encoding)
            self.reader = csv.reader(csv_file, dialect=dialect, **keywords)

        def next(self):
            row = self.reader.next()
            return [six.text_type(item, 'utf-8') for item in row]

        def __iter__(self):
            return self

    def _key_to_str_value_map(key_to_value_map):
        """
        Similar to ``key_to_value_map`` but with values of type `unicode`
        converted to `str` because in Python 2 `csv.reader` can only process
        byte strings for formatting parameters, e.g. delimiter=b';' instead of
        delimiter=u';'. This quickly becomes an annoyance to the caller, in
        particular with `from __future__ import unicode_literals` enabled.
        """
        return dict((key, value if not isinstance(value, six.text_type) else str(value))
                    for key, value in key_to_value_map.items())

    def _delimited_rows(delimited_path, encoding, **keywords):
        with io.open(delimited_path, 'rb') as delimited_file:
            str_keywords = _key_to_str_value_map(keywords)
            unicode_csv_reader = _UnicodeReader(delimited_file, encoding=encoding, **str_keywords)
            try:
                for row in unicode_csv_reader:
                    yield row
            except csv.Error as error:
                _raise_delimited_data_format_error(delimited_path, unicode_csv_reader.reader, error)


def delimited_rows(delimited_path, data_format):
    if data_format.escape_character == data_format.quote_character:
        doublequote = False
        escapechar = None
    else:
        doublequote = True
        escapechar = data_format.escape_character

    # HACK: Ignore DataFormat.line_delimiter because at least until Python 3.4 csv.reader ignores it anyway.
    csv_reader = _delimited_rows(delimited_path, encoding=data_format.encoding, delimiter=data_format.item_delimiter,
                           doublequote=doublequote, escapechar=escapechar, quotechar=data_format.quote_character,
                           skipinitialspace=data_format.skip_initial_space, strict=True)
    for row in csv_reader:
        yield row


def ods_rows(source_ods_path, sheet=1):
    """
    Rows stored in ODS document ``source_ods_path`` in ``sheet``.
    """
    assert sheet >= 1

    def ods_content_root(source_ods_path):
        """
        `ElementTree` for content.xml in `source_ods_path`.
        """
        assert source_ods_path is not None

        location = errors.Location(source_ods_path)
        try:
            with zipfile.ZipFile(source_ods_path, "r") as zip_archive:
                try:
                    xml_data = zip_archive.read("content.xml")
                except Exception as error:
                    raise errors.DataFormatError('cannot extract content.xml for ODS spreadsheet: %s' % error, location)
        except errors.DataFormatError:
            raise
        except Exception as error:
            raise errors.DataFormatError('cannot uncompress ODS spreadsheet: %s' % error, location)

        with io.BytesIO(xml_data) as xml_stream:
            try:
                tree = ElementTree.parse(xml_stream)
            except Exception as error:
                raise errors.DataFormatError('cannot parse content.xml: %s' % error, location)

        return tree.getroot()

    content_root = ods_content_root(source_ods_path)
    table_elements = list(
        content_root.findall('office:body/office:spreadsheet/table:table', namespaces=_OOO_NAMESPACES))
    table_count = len(table_elements)
    if table_count < sheet:
        error_message = 'ODS must contain at least %d sheet(s) instead of just %d' % (sheet, table_count)
        raise errors.DataFormatError(error_message, errors.Location(source_ods_path))
    table_element = table_elements[sheet - 1]
    location = errors.Location(source_ods_path, has_cell=True, has_sheet=True)
    for _ in range(sheet - 1):
        location.advance_sheet()
    for table_row in table_element.findall('table:table-row', namespaces=_OOO_NAMESPACES):
        row = []
        for table_cell in table_row.findall('table:table-cell', namespaces=_OOO_NAMESPACES):
            repeated_text = table_cell.attrib.get(_NUMBER_COLUMNS_REPEATED, '1')
            try:
                repeated_count = int(repeated_text)
                if repeated_count < 1:
                    raise errors.DataFormatError(
                        'table:number-columns-repeated is %r but must be at least 1' % repeated_text, location)
            except ValueError:
                raise errors.DataFormatError(
                    'table:number-columns-repeated is %r but must be an integer' % repeated_text, location)
            text_p = table_cell.find('text:p', namespaces=_OOO_NAMESPACES)
            if text_p is None:
                cell_value = ''
            else:
                cell_value = text_p.text
            row.extend([cell_value] * repeated_count)
            location.advance_cell(repeated_count)
        yield row
        location.advance_line()


def fixed_rows(fixed_path, encoding, field_name_and_lengths, line_delimiter='any'):
    """
    Rows found in file `fixed_path` using `encoding`. The name and (fixed)
    length of the fields for each row are specified as a list of tuples
    `(name, length)`. Each row can end with a line feed unless
    `line_delimiter=None`. Valid values are: `'\n'`, `'\r'` and `'\r\n'`, in
    which case other values result in a `errors.DataFormatError`.
    Additionally `'any'` accepts any of the previous values.
    """
    assert fixed_path is not None
    assert encoding is not None
    for name, length in field_name_and_lengths:
        assert name is not None
        assert length >= 1, 'length for %s must be at least 1 but is %s' % (name, length)
    assert line_delimiter in _VALID_FIXED_LINE_DELIMITERS, \
        'line_delimiter=%r but must be one of: %s' % (line_delimiter, _VALID_FIXED_LINE_DELIMITERS)

    location = errors.Location(fixed_path, has_column=True)
    fixed_file = None  # Predefine variable for access in local function.

    def _has_data_after_skipped_line_delimiter():
        """
        If `fixed_file` has data, assume they are a line delimiter as specified
        by `line_delimiter` and read and validate them.

        In case `line_delimiter` is `None`, the result is
        """
        assert location is not None
        assert line_delimiter is not None  # `None` does not need any skipping.
        assert line_delimiter in _VALID_FIXED_LINE_DELIMITERS

        result = True
        if line_delimiter is not None:
            if line_delimiter in ('\n', '\r', 'any'):
                actual_line_delimiter = fixed_file.read(1)
            elif line_delimiter == '\r\n':
                actual_line_delimiter = fixed_file.read(2)
            if (line_delimiter == 'any') and (actual_line_delimiter != ''):
                # Process the optional second character for 'any'.
                if actual_line_delimiter not in '\n\r':
                    raise errors.DataFormatError(
                        'line delimiter is %r but must be one of: %s' %
                        (actual_line_delimiter, _tools.humanReadableList(('\n', '\r', '\r\n'))), location)
                if actual_line_delimiter == '\r':
                    next_character = fixed_file.read(1)
                    if next_character == '\n':
                        actual_line_delimiter += next_character
                    elif next_character == '':
                        result = False
                    else:
                        # Discard the last character read because it is unrelated to line separators.
                        fixed_file.seek(-1, os.SEEK_CUR)
            if actual_line_delimiter == '':
                result = False
            elif (line_delimiter != 'any') and (actual_line_delimiter != line_delimiter):
                raise errors.DataFormatError(
                    'line delimiter is %r but must be %r' % (actual_line_delimiter, line_delimiter), location)
        return result

    has_data = True
    with io.open(fixed_path, 'r', encoding=encoding) as fixed_file:
        while has_data:
            field_index = 0
            row = []
            for field_name, field_length in field_name_and_lengths:
                item = fixed_file.read(field_length)
                item_length = len(item)
                if item_length == 0:
                    if field_index > 0:
                        raise errors.DataFormatError(
                            'input must contain data for field %s (and any subsequent ones)', location)
                    # End of input reached.
                    has_data = False
                elif item_length == field_length:
                    row.append(item)
                    location.advance_column(field_length)
                    field_index += 1
                else:
                    raise errors.DataFormatError(
                        'cannot read field %s: need %d characters but found only %d: %r'
                        % (field_name, field_length, item_length, item), location)
            if has_data and not _has_data_after_skipped_line_delimiter():
                has_data = False
            if len(row) > 0:
                yield row
                location.advance_line()
