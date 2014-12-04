"""
Various internal utility functions.

Note: The original source code for `UTF8Recoder`, `UnicodeReader` and `UnicodeWriter` is available
from the Python documentation.
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
import codecs
import csv
import datetime
import decimal
import errno
import keyword
import logging
import os
import platform
import re
import io
import token
import tokenize
import unicodedata
import xlrd
import zipfile
from xml.etree import ElementTree

from cutplace import errors


# Mapping for value of --log to logging level.
LOG_LEVEL_NAME_TO_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

NUMBER_DECIMAL_COMMA = "decimalComma"
NUMBER_DECIMAL_POINT = "decimalPoint"
NUMBER_INTEGER = "integer"

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


def mkdirs(folder):
    """
    Like ``os.mkdirs()`` but does not raise an `OSError` if ``folder`` already exists.
    """
    assert folder is not None

    try:
        os.makedirs(folder)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise


def attemptToRemove(filePath):
    """
    Like ``os.remove()`` but does not raise an `OSError` if ``filePath`` does not exist.
    """
    assert filePath is not None

    try:
        os.remove(filePath)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise


def validatedPythonName(name, value):
    """
    Validated and cleaned up `value` that represents a Python name with any whitespace removed.
    If validation fails, raise `NameError` with mentioning ``name`` as the name under which
    ``value``  is known to the user.
    """
    assert name
    assert value is not None

    readable = io.StringIO(value.strip())
    toky = tokenize.generate_tokens(readable.readline)
    nextToken = next(toky)
    nextType = nextToken[0]
    result = nextToken[1]
    if tokenize.ISEOF(nextType):
        raise NameError("%s must not be empty but was: %r" % (name, value))
    if nextType != token.NAME:
        raise NameError("%s must contain only ASCII letters, digits and underscore (_) but is: %r"
                % (name, value))
    secondToken = next(toky)
    secondTokenType = secondToken[0]
    if not tokenize.ISEOF(secondTokenType):
        raise NameError("%s must be a single word, but after %r there also is %r" % (name, result, secondToken[1]))
    return result


def camelized(key, firstIsLower=False):
    """
    Camelized name of possibly multiple words separated by blanks that can be used for variables.
    """
    assert key is not None
    assert key == key.strip(), "key must be trimmed"
    result = ""
    for part in key.split():
        result += part[0].upper() + part[1:].lower()
    if firstIsLower and result:
        result = result[0].lower() + result[1:]
    return result


def decamelized(name):
    """
    Decamlized, all lower case ``name`` with former upper case letters marking words separated by blanks.

    Examples:

    >>> decamelized('some')
    'some'
    >>> decamelized('someMore')
    'some more'
    >>> decamelized('EvenMore')
    'Even more'
    >>> decamelized('')
    ''
    """
    assert name is not None
    assert name == name.strip(), "name must be trimmed"
    if name:
        result = name[0]
        for c in name[1:]:
            if c.isdigit() or c.islower():
                result += c
            else:
                result += " " + c.lower()
    else:
        result = ""
    return result


def platformVersion():
    macVersion = platform.mac_ver()
    if (macVersion[0]):
        result = "Mac OS %s (%s)" % (macVersion[0], macVersion[2])
    else:
        result = platform.platform()
    return result


def pythonVersion():
        return platform.python_version()


def humanReadableList(items):
    """
    All values in `items` in a human readable form. This is meant to be used in error messages, where
    dumping "%r" to the user does not cut it.
    """
    assert items is not None
    itemCount = len(items)
    if itemCount == 0:
        result = ""
    elif itemCount == 1:
        result = "%r" % items[0]
    else:
        result = ""
        for itemIndex in range(itemCount):
            if itemIndex == itemCount - 1:
                result += " or "
            elif itemIndex > 0:
                result += ", "
            result += "%r" % items[itemIndex]
        assert result
    assert result is not None
    return result


def tokenizeWithoutSpace(text):
    """
    ``text`` split into token with any white space tokens removed.
    """
    assert text is not None
    for toky in tokenize.generate_tokens(io.StringIO(text).readline):
        tokyType = toky[0]
        tokyText = toky[1]
        if ((tokyType != token.INDENT) and tokyText.strip()) or (tokyType == token.ENDMARKER):
            yield toky


def tokenText(toky):
    assert toky is not None
    tokyType = toky[0]
    tokyText = toky[1]
    if tokyType == token.STRING:
        result = tokyText[1:-1]
    else:
        result = tokyText
    return result


def isEofToken(someToken):
    """
    True if `someToken` is a token that represents an "end of file".
    """
    assert someToken is not None
    return tokenize.ISEOF(someToken[0])


def isCommaToken(someToken):
    """
    True if `someToken` is a token that represents a comma (,).
    """
    assert someToken
    return (someToken[0] == token.OP) and (someToken[1] == ",")


def withSuffix(path, suffix=""):
    """
    Same as `path` but with suffix changed to `suffix`.

    Examples:

    >>> withSuffix("eggs.txt", ".rst")
    'eggs.rst'
    >>> withSuffix("eggs.txt", "")
    'eggs'
    >>> withSuffix(os.path.join("spam", "eggs.txt"), ".rst")
    'spam/eggs.rst'
    """
    assert path is not None
    assert suffix is not None
    result = os.path.splitext(path)[0]
    if suffix:
        result += suffix
    return result


def asciified(text):
    """
    Similar to ``text`` but with none ASCII letters replaced by their decomposed ASCII
    equivalent.
    """
    assert text is not None
    if not isinstance(text, str):
        raise ValueError("text must be unicode instead of %s" % type(text))
    result = ""
    for ch in text:
        decomp = unicodedata.decomposition(ch)
        if decomp:
            result += chr(int(decomp.split()[0], 16))
        else:
            result += ch
    return result


def namified(text):
    """
    Similar to ``text`` with possible modifications to ensure that it can be used as
    Python variable name.
    """
    assert text is not None
    result = ""
    asciifiedText = asciified(text.strip())
    wasUnderscore = False
    for ch in asciifiedText:
        isUnderscore = (ch == "_")
        if ch.isalnum() or isUnderscore:
            if not (wasUnderscore and isUnderscore):
                result += ch
            wasUnderscore = isUnderscore
        elif not wasUnderscore:
            result += "_"
            wasUnderscore = True
    if not result or result[0].isdigit():
        result = "x" + result
    if keyword.iskeyword(result):
        result += "_"
    assert result
    return result


def numbered(value, decimalSeparator=".", thousandsSeparator=","):
    """
    Tuple describing ``value`` as type and numberized value.
    """
    assert value is not None
    assert decimalSeparator in (".", ",")
    assert thousandsSeparator in (".", ",")
    assert decimalSeparator != thousandsSeparator
    resultType = None
    resultUsesThousandsSeparator = False
    resultValue = value
    lastThousandsSeparatorIndex = None
    hasBrokenThousandsSeparator = False
    try:
        resultValue = int(value)
        resultType = NUMBER_INTEGER
    except ValueError:
        decimalText = ""
        decimalDelimiterCount = 0
        charIndex = 0
        charCount = len(value)
        while (charIndex < charCount) and (decimalDelimiterCount <= 1) and not hasBrokenThousandsSeparator:
            charToExamine = value[charIndex]
            if charToExamine == thousandsSeparator:
                if lastThousandsSeparatorIndex is not None:
                    if (charIndex - lastThousandsSeparatorIndex) == 4:
                        resultUsesThousandsSeparator = True
                    else:
                        hasBrokenThousandsSeparator = True
                        resultUsesThousandsSeparator = False
                else:
                    resultUsesThousandsSeparator = True
                lastThousandsSeparatorIndex = charIndex
            else:
                if charToExamine == decimalSeparator:
                    charToExamine = "."
                    decimalDelimiterCount += 1
                decimalText += charToExamine
            charIndex += 1
        if (decimalDelimiterCount <= 1) and not hasBrokenThousandsSeparator:
            try:
                resultValue = decimal.Decimal(decimalText)
                if decimalSeparator == ".":
                    resultType = NUMBER_DECIMAL_POINT
                else:
                    resultType = NUMBER_DECIMAL_COMMA
            except decimal.InvalidOperation:
                # Keep default result.
                pass
    return resultType, resultUsesThousandsSeparator, resultValue


def _excelCellValue(cell, datemode):
    """
    The value of ``cell`` as text taking into account the way excel encodes dates and times.

    Numeric Excel types (Currency,  Fractional, Number, Percent, Scientific) simply yield the decimal number
    without any special formatting.

    Dates result in a text using the format "YYYY-MM-DD", times in a text using the format "hh:mm:ss".

    Boolean yields "0" or "1".

    Formulas are evaluated and yield the respective result.
    """
    assert cell is not None

    # Just import without sanitizing the error message. If we got that far, the import should have worked
    # already.
    import xlrd

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


def excel_rows(source_path):
    location = errors.InputLocation(source_path, has_cell=True)
    try:
        book = xlrd.open_workbook(source_path)
        sheet = book.sheet_by_index(0)
        datemode = book.datemode
        for y in range(sheet.nrows):
            row = []
            for x in range(sheet.ncols):
                row.append(_excelCellValue(sheet.cell(y, x), datemode))
                location.advance_cell()
            yield row
            location.advance_line()
    except xlrd.XLRDError as error:
        raise errors.DataFormatError('cannot read Excel file: %s' % error, location)


def delimited_rows(source_path, data_format):
    with open(source_path, encoding=data_format.encoding) as csv_file:
        if data_format.escape_character == data_format.quote_character:
            doublequote = False
            escapechar = None
        else:
            doublequote = True
            escapechar = data_format.escape_character

        # HACK: Ignore DataFormat.line_delimiter because at least until Python 3.4 csv.reader ignores it anyway.
        csv_reader = csv.reader(csv_file, delimiter=data_format.item_delimiter, doublequote=doublequote,
            escapechar=escapechar, quotechar=data_format.quote_character,
            skipinitialspace=data_format.skip_initial_space, strict=True)

        # TODO: raise DataFormatError on basic CVS format violations (e.g. unterminated quotes).
        for row in csv_reader:
            yield row


def ods_content_root(source_ods_path):
    """
    `ElementTree` for content.xml in `source_ods_path`.
    """
    assert source_ods_path is not None

    location = errors.InputLocation(source_ods_path)
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


def ods_rows(source_ods_path, sheet=1):
    """
    Rows stored in ODS document ``source_ods_path`` in ``sheet``.
    """
    assert sheet >= 1
    content_root = ods_content_root(source_ods_path)
    table_elements = list(content_root.findall('office:body/office:spreadsheet/table:table', namespaces=_OOO_NAMESPACES))
    table_count = len(table_elements)
    if table_count < sheet:
        raise ValueError('ODS must contain at least %d sheet(s) instead of just %d' % (sheet, table_count))
    table_element = table_elements[sheet - 1]
    location = errors.InputLocation(source_ods_path, has_cell=True, has_sheet=True)
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
