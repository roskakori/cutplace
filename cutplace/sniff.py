"""
Heuristic data analysis to figure out file types and field formats.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
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
import decimal
import logging
import string

import data
import fields
import tools
import _tools

_log = logging.getLogger("cutplace")

"""
Pseudo data format name to indicate the the format should be sniffed.
"""
FORMAT_AUTO = data.ANY

"""
The encoding to be used if no encoding is specified within the keyword
parameters of the functions of this module.
"""
DEFAULT_ENCODING = "ascii"
DEFAULT_ESCAPE_CHARACTER = "\""
DEFAULT_HEADER = "0"
DEFAULT_ITEM_DELIMITER = data.ANY
DEFAULT_LINE_DELIMITER = data.ANY
DEFAULT_QUOTE_CHARACTER = "\""

_ENCODING = _tools.camelized(data.KEY_ENCODING, True)
_ESCAPE_CHARACTER = _tools.camelized(data.KEY_ESCAPE_CHARACTER, True)
_HEADER = _tools.camelized(data.KEY_HEADER, True)
_ITEM_DELIMITER = _tools.camelized(data.KEY_ITEM_DELIMITER, True)
_LINE_DELIMITER = _tools.camelized(data.KEY_LINE_DELIMITER, True)
_QUOTE_CHARACTER = _tools.camelized(data.KEY_QUOTE_CHARACTER, True)

CR = "\r"
LF = "\n"
CRLF = CR + LF
_VALID_LINE_DELIMITERS = [data.ANY, CR, CRLF, LF]

_LINE_DELIMITER_TO_NAME_MAP = {
    CR: data.CR,
    CRLF: data.CRLF,
    LF: data.LF,
}

# Header used by zipped ODS content.
_ODS_HEADER = "PK\x03\x04"

# Header used by Excel (and other MS Office applications).
_EXCEL_HEADER = "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


class CutplaceSniffError(tools.CutplaceError):
    """
    Error to indicate that the format of some content could not be sniffed.
    """


def createDataFormat(readable, **keywords):
    """
    Data format describing the contents of ``readable``, which should be a
    a raw binary input stream as returned by ``open(..., 'rb')``. Do not use
    ``codecs.open(...)`` because it returns Unicode strings instead of raw
    strings.

    Supported formats are delimited data (such as CSV), ODS and Excel.
    """
    assert readable is not None
    encoding = keywords.get("encoding", DEFAULT_ENCODING)
    assert encoding is not None

    icdHeader = readable.read(4)
    _log.debug(u"header=%r", icdHeader)
    if _tools.isEqualBytes(icdHeader, _ODS_HEADER):
        # Consider ICD to be ODS.
        dataFormatName = data.FORMAT_ODS
    else:
        icdHeader += readable.read(4)
        assert isinstance(icdHeader, str), u"icdHeader=%r but must be a string; use open(..., 'rb') instead of codecs.open()" % icdHeader
        assert isinstance(_EXCEL_HEADER, str), u"_EXCEL_HEADER=%r" % _EXCEL_HEADER
        if _tools.isEqualBytes(icdHeader, _EXCEL_HEADER):
            # Consider ICD to be Excel.
            dataFormatName = data.FORMAT_EXCEL
        else:
            # Consider ICD to be CSV.
            dataFormatName = data.FORMAT_DELIMITED
    result = data.createDataFormat(dataFormatName)
    if result.name == data.FORMAT_DELIMITED:
        readable.seek(0)
        options = delimitedOptions(readable, **keywords)
        for key, value in options.items():
            propertyName = _tools.decamelized(key)
            if key == _LINE_DELIMITER:
                value = _LINE_DELIMITER_TO_NAME_MAP[value]
            result.set(propertyName, value)
    readable.seek(0)
    return result


def createReader(readable, **keywords):
    """
    A reader fitting the contents of ``readable``. Supported formats are
    delimited data (such as CSV), ODS and Excel. When iterating the reader,
    it returns a Python array for each row of data.
    """
    # TODO: Get rid of circular import.
    import _parsers

    assert readable is not None
    encoding = keywords.get("encoding", DEFAULT_ENCODING)
    assert encoding is not None

    result = None
    icdHeader = readable.read(4)
    _log.debug(u"header=%r", icdHeader)
    if icdHeader == _ODS_HEADER:
        # Consider ICD to be ODS.
        readable.seek(0)
        result = _parsers.odsReader(readable)
    else:
        icdHeader += readable.read(4)
        readable.seek(0)
        if _tools.isEqualBytes(icdHeader, _EXCEL_HEADER):
            # Consider ICD to be Excel.
            result = _parsers.excelReader(readable)
        else:
            # Consider ICD to be CSV.
            dialect = _parsers.DelimitedDialect()
            dialect.lineDelimiter = _parsers.AUTO
            dialect.itemDelimiter = _parsers.AUTO
            dialect.quoteChar = "\""
            dialect.escapeChar = "\""
            result = _parsers.delimitedReader(readable, dialect, encoding)
    return result


def delimitedOptions(readable, **keywords):
    """
    Dictionary containing the delimited options as derived from ``readable`` and ``keywords``.

    Possible values for ``keywords`` and the keys in the result are:

      *  ``encoding``
      *  ``escapeCharacter``
      *  ``header``
      *  ``itemDelimiter``
      *  ``lineDelimiter``
      *  ``quoteCharacter``
    """
    assert readable is not None
    encoding = keywords.get(_ENCODING, DEFAULT_ENCODING)
    assert encoding is not None
    escapeCharacter = keywords.get(_ESCAPE_CHARACTER, DEFAULT_ESCAPE_CHARACTER)
    if escapeCharacter is None:
        escapeCharacter = DEFAULT_ESCAPE_CHARACTER
    # assert escapeCharacter is not None
    itemDelimiter = keywords.get(_ITEM_DELIMITER, DEFAULT_ITEM_DELIMITER)
    assert itemDelimiter is not None
    lineDelimiter = keywords.get(_LINE_DELIMITER, DEFAULT_LINE_DELIMITER)
    assert lineDelimiter in _VALID_LINE_DELIMITERS
    quoteCharacter = keywords.get(_QUOTE_CHARACTER, DEFAULT_QUOTE_CHARACTER)
    assert quoteCharacter is not None
    header = keywords.get(_HEADER, DEFAULT_HEADER)

    # Automatically set line and item delimiter.
    # TODO: Use a more intelligent logic. Csv.Sniffer would be nice,
    # but not all test cases work with it.
    if (lineDelimiter == data.ANY) or (itemDelimiter == data.ANY):
        oldPosition = readable.tell()
        sniffedText = readable.read(16384)
        readable.seek(oldPosition)
    if lineDelimiter == data.ANY:
        crLfCount = sniffedText.count(CRLF)
        crCount = sniffedText.count(CR) - crLfCount
        lfCount = sniffedText.count(LF) - crLfCount
        if (crCount > crLfCount):
            if (crCount > lfCount):
                actualLineDelimiter = CR
            else:
                actualLineDelimiter = CRLF
        else:
            if (crLfCount > lfCount):
                actualLineDelimiter = CRLF
            else:
                actualLineDelimiter = LF
        _log.debug(u"  detected line delimiter: %r", actualLineDelimiter)
    else:
        actualLineDelimiter = lineDelimiter
    if itemDelimiter == data.ANY:
        itemDelimiterToCountMap = {
            ",": sniffedText.count(","),
            ";": sniffedText.count(";"),
            ":": sniffedText.count(":"),
            "\t": sniffedText.count("\t"),
            "|": sniffedText.count("|")
        }
        actualItemDelimiter = ','
        delimiterCount = itemDelimiterToCountMap[","]
        for possibleItemDelimiter in itemDelimiterToCountMap:
            if itemDelimiterToCountMap[possibleItemDelimiter] > delimiterCount:
                delimiterCount = itemDelimiterToCountMap[possibleItemDelimiter]
                actualItemDelimiter = possibleItemDelimiter
            _log.debug(u"  detected item delimiter: %r", actualItemDelimiter)
    else:
        actualItemDelimiter = itemDelimiter

    result = {
        _ENCODING: encoding,
        _ESCAPE_CHARACTER: escapeCharacter,
        _ITEM_DELIMITER: actualItemDelimiter,
        _LINE_DELIMITER: actualLineDelimiter,
        _QUOTE_CHARACTER: quoteCharacter
    }
    if header != DEFAULT_HEADER:
        result[_HEADER] = header
    return result


class _ColumnSniffInfo(object):
    def __init__(self, columnIndex, dataFormat):
        assert columnIndex >= 0
        assert dataFormat is not None

        self.columnIndex = columnIndex
        self.dataFormat = dataFormat
        self.name = "column_" + _tools.basedText(columnIndex, 26, string.ascii_lowercase)
        self.emptyCount = 0
        self.decimalCount = 0
        self.longCount = 0
        self.maxLength = 0
        self.minLength = None
        self.textCount = 0
        self.distinctValues = set([])

    def _isLong(self, value):
        assert value is not None
        try:
            long(value)
            result = True
        except ValueError:
            result = False
        return result

    def _isDecimal(self, value):
        assert value is not None
        # TODO: Consider thousands and decimal separator.
        try:
            decimal.Decimal(value)
            result = True
        except decimal.InvalidOperation:
            result = False
        return result

    def process(self, value):
        assert value is not None

        length = len(value)
        if length:
            if not self.textCount:
                if self._isLong(value):
                    self.longCount += 1
                else:
                    self.textCount += 1
            if (self.minLength is None) or (length < self.minLength):
                self.minLength = length
            if length > self.maxLength:
                self.maxLength = length
            if value not in self.distinctValues:
                self.distinctValues |= set([value])
        else:
            self.emptyCount += 1

    def asFieldFormat(self):
        isAllowedToBeEmpty = (self.emptyCount > 0)
        lengthText = ""
        if self.minLength == self.maxLength:
            lengthText = unicode(self.minLength)
        else:
            if self.minLength:
                lengthText += unicode(self.minLength)
            lengthText += ":%d" % self.maxLength

        # TODO: Detect decimal and integer format.
        # TODO: Detect date format.
        result = fields.TextFieldFormat(self.name, isAllowedToBeEmpty, lengthText, "", self.dataFormat)
        return result


def createCidRows(readable, **keywords):
    """
    Create rows for an ICD by examining the contents of ``readable``.

    Optional keyword parameters are:

      * ``encoding`` - the character encoding to be used in case ``readable``
        contains delimited data.
      * ``dataFormat`` - the data format to be assumed; default: `FORMAT_AUTO`.
      * ``header`` - number of header rows to ignore for data analysis;
        default: 0.
      * ``stopAfter`` - number of data rows after which to stop analyzing;
        0 means "analyze all data"; default: 0.
      * ``fieldNames`` - Python names to refer to the fields. If this is a list of
        strings, each string represents a field name. If this is a single
        string, split it using comma (,) as separator to get to the names. If
        this is ``None`` (the default), use the last column of the ``header``
        as names. If ``header`` is ``None``, use generated field names such as
        'column_a', 'column_b' and so on.
    """
    assert readable is not None
    dataFormat = keywords.get("dataFormat", FORMAT_AUTO)
    assert dataFormat is not None
    encoding = keywords.get(_ENCODING, DEFAULT_ENCODING)
    assert encoding is not None
    dataRowsToStopAfter = keywords.get("stopAfter", 0)
    assert dataRowsToStopAfter >= 0
    headerRowsToSkip = keywords.get("header", 0)
    assert headerRowsToSkip >= 0
    fieldNames = keywords.get("fieldNames")
    if isinstance(fieldNames, basestring):
        fieldNames = [name.strip() for name in fieldNames.split(",")]
    elif fieldNames is not None:
        assert isinstance(fieldNames, list), u"field names must be a list or string but is: %s" % type(fieldNames)

    NO_COUNT = -1

    _log.debug(u"find longest segment of rows with same column count")
    currentSegmentColumnCount = None
    longestSegmentColumnCount = NO_COUNT
    longestSegmentRowCount = NO_COUNT
    currentSegmentRowCount = 0
    rowIndex = 0
    rowIndexWhereCurrentSegmentStarted = 0
    rowIndexWhereLongestSegmentStarts = None
    # TODO: Cleanup code: calling both createDataFormat and createReader causes the data format to be analyzed twice.
    dataFormat = createDataFormat(readable, **keywords)
    readable.seek(0)
    reader = createReader(readable, **keywords)
    isFirstRow = True
    isReadFieldNamesFromHeader = (not fieldNames and headerRowsToSkip)
    for rowToAnalyze in reader:
        columnCount = len(rowToAnalyze)
        if isFirstRow:
            currentSegmentColumnCount = columnCount
        else:
            isFirstRow = False
        if isReadFieldNamesFromHeader and (rowIndex == headerRowsToSkip - 1):
            fieldNames = rowToAnalyze
        if (rowIndex >= headerRowsToSkip) and (columnCount != currentSegmentColumnCount):
            _log.debug(u"  segment starts in row %d after %d rows", rowIndex, currentSegmentRowCount)
            if currentSegmentRowCount > longestSegmentRowCount:
                rowIndexWhereLongestSegmentStarts = rowIndexWhereCurrentSegmentStarted
                longestSegmentRowCount = currentSegmentRowCount
                longestSegmentColumnCount = currentSegmentColumnCount
            rowIndexWhereCurrentSegmentStarted = rowIndex
            currentSegmentRowCount = 0
            currentSegmentColumnCount = columnCount
        else:
            currentSegmentRowCount += 1
        rowIndex += 1

    # Validate field names.
    if fieldNames is not None:
        if isReadFieldNamesFromHeader:
            location = tools.InputLocation(readable, hasCell=True)
            location.advanceLine(headerRowsToSkip)
        else:
            location = None
        if not fieldNames:
            raise data.DataFormatSyntaxError(u"the field names specified must contain at least 1 name", location)
        uniquefieldNames = set()
        for nameIndex in range(len(fieldNames)):
            fieldNameToCheck = fieldNames[nameIndex]
            if isReadFieldNamesFromHeader:
                fieldNameToCheck = _tools.namified(fieldNameToCheck)
            fieldNameToCheck = fields.validatedFieldName(fieldNameToCheck, location)
            if fieldNameToCheck in uniquefieldNames:
                raise fields.FieldSyntaxError(u"field name must be unique: %s" % fieldNameToCheck, location)
            fieldNames[nameIndex] = fieldNameToCheck
            uniquefieldNames.add(fieldNameToCheck)
            if location:
                location.advanceCell()

    # Handle the case that the whole file can be one large segment.
    _log.debug(u"last segment started in row %d and lasted for %d rows", rowIndexWhereCurrentSegmentStarted, currentSegmentRowCount)
    if currentSegmentRowCount > longestSegmentRowCount:
        rowIndexWhereLongestSegmentStarts = rowIndexWhereCurrentSegmentStarted
        longestSegmentRowCount = currentSegmentRowCount
        longestSegmentColumnCount = currentSegmentColumnCount

    if longestSegmentRowCount < 1:
        raise CutplaceSniffError(u"content must contain data for format to be sniffed")
    _log.debug(u"found longest segment starting in row %d lasting for %d rows having %d columns",
        rowIndexWhereLongestSegmentStarts, longestSegmentRowCount, longestSegmentColumnCount)

    assert rowIndexWhereLongestSegmentStarts is not None
    _log.debug(u"skip %d rows until longest segment starts", rowIndexWhereLongestSegmentStarts)
    readable.seek(0)
    reader = createReader(readable, **keywords)
    rowIndex = 0
    location = tools.InputLocation(readable)
    while rowIndex < rowIndexWhereLongestSegmentStarts:
        reader.next()
        location.advanceLine()
        rowIndex += 1

    _log.info(u"analyze longest segment of rows with same column count")
    columnInfos = []
    for columnIndex in range(longestSegmentColumnCount):
        columnInfoToAppend = _ColumnSniffInfo(columnIndex, dataFormat)
        if fieldNames:
            columnInfoToAppend.name = fieldNames[columnIndex]
        columnInfos.append(columnInfoToAppend)
    rowIndex = 0
    while rowIndex < longestSegmentRowCount:
        rowToAnalyze = reader.next()
        if rowIndex >= headerRowsToSkip:
            columnCountOfRowToAnalyze = len(rowToAnalyze)
            if columnCountOfRowToAnalyze != longestSegmentColumnCount:
                raise CutplaceSniffError(u"data must not change between sniffer passes, but row %d now has %d columns instead of %d" \
                    % (rowIndex + 1, columnCountOfRowToAnalyze, longestSegmentColumnCount), location)
            for itemIndex in range(longestSegmentColumnCount):
                value = rowToAnalyze[itemIndex]
                columnInfos[itemIndex].process(value)
        location.advanceLine()
        rowIndex += 1

    for columnIndex in range(longestSegmentColumnCount):
        _log.debug(u"  %s" % columnInfos[columnIndex].asFieldFormat())

    icdRows = []
    icdRows.append(["", "Interface: <Name>"])
    icdRows.append([])
    for dataFormatRow in dataFormat.asIcdRows():
        dataFormatCsvRow = ['d']
        dataFormatCsvRow.extend(dataFormatRow)
        icdRows.append(dataFormatCsvRow)
    icdRows.append([])

    icdRows.append(["", "Field", "Example", "Empty?", "Length", "Type", "Rule"])
    for columnInfo in columnInfos:
        fieldFormat = columnInfo.asFieldFormat()
        fieldRow = ["f"]
        fieldRow.extend(fieldFormat.asIcdRow())
        icdRows.append(fieldRow)
    # TODO: Create interface.InterfaceControlDocument and use it as icdRows.
    return icdRows
