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
DEFAULT_ITEM_DELIMITER = data.ANY
DEFAULT_LINE_DELIMITER = data.ANY
DEFAULT_QUOTE_CHARACTER = "\""

_ENCODING = _tools.camelized(data.KEY_ENCODING, True)
_ESCAPE_CHARACTER = _tools.camelized(data.KEY_ESCAPE_CHARACTER, True)
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
    Data format describing the contents of ``readable``.

    Supported formats are delimited data (such as CSV), ODS and Excel.
    """
    assert readable is not None
    encoding = keywords.get("encoding", DEFAULT_ENCODING)
    assert encoding is not None

    icdHeader = readable.read(4)
    _log.debug("header=%r", icdHeader)
    if _tools.isEqualBytes(icdHeader, _ODS_HEADER):
        # Consider ICD to be ODS.
        dataFormatName = data.FORMAT_ODS
    else:
        icdHeader += readable.read(4)
        assert isinstance(icdHeader, str), "icdHeader=%r" % icdHeader
        assert isinstance(_EXCEL_HEADER, str), "_EXCEL_HEADER=%r" % _EXCEL_HEADER
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
    _log.debug("header=%r", icdHeader)
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
      *  ``escapeCharacter`
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
        _log.debug("  detected line delimiter: %r", actualLineDelimiter)
    else:
        actualLineDelimiter = lineDelimiter
    if itemDelimiter == data.ANY:
        itemDelimiterToCountMap = {",":sniffedText.count(","),
            ";":sniffedText.count(";"),
            ":":sniffedText.count(":"),
            "\t":sniffedText.count("\t"),
            "|":sniffedText.count("|")
        }
        actualItemDelimiter = ','
        delimiterCount = itemDelimiterToCountMap[","]
        for possibleItemDelimiter in itemDelimiterToCountMap:
            if itemDelimiterToCountMap[possibleItemDelimiter] > delimiterCount:
                delimiterCount = itemDelimiterToCountMap[possibleItemDelimiter]
                actualItemDelimiter = possibleItemDelimiter
            _log.debug("  detected item delimiter: %r", actualItemDelimiter)
    else:
        actualItemDelimiter = itemDelimiter

    result = {
        _ENCODING: encoding,
        _ESCAPE_CHARACTER: escapeCharacter,
        _ITEM_DELIMITER: actualItemDelimiter,
        _LINE_DELIMITER: actualLineDelimiter,
        _QUOTE_CHARACTER: quoteCharacter
    }
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

def createInterfaceControlDocument(readable, **keywords):
    """
    Create an ICD by examining the contents of ``readable``.

    Optional keyword parameters are:

      * ``encoding`` - the character encoding to be used in case ``readable``
        contains delimited data.
      * ``dataFormat`` - the data format to be assumed; default: `FORMAT_AUTO`.
      * ``header`` - number of header rows to ignore for data analysis;
        default: 0.
      * ``stopAfter`` - number of data rows after which to stop analyzing;
        0 means "analyze all data"; default: 0.
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

    NO_COUNT = -1

    _log.debug("find longest segment of rows with same column count")
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
    for rowToAnalyze in reader:
        columnCount = len(rowToAnalyze)
        if isFirstRow:
            currentSegmentColumnCount = columnCount
        else:
            isFirstRow = False
        if columnCount != currentSegmentColumnCount:
            _log.debug("  segment starts in row %d after %d rows", rowIndex, currentSegmentRowCount)
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

    # Handle the case that the whole file can be one large segment.
    _log.debug("last segment started in row %d and lasted for %d rows", rowIndexWhereCurrentSegmentStarted, currentSegmentRowCount)
    if currentSegmentRowCount > longestSegmentRowCount:
        rowIndexWhereLongestSegmentStarts = rowIndexWhereCurrentSegmentStarted
        longestSegmentRowCount = currentSegmentRowCount
        longestSegmentColumnCount = currentSegmentColumnCount

    if longestSegmentRowCount < 1:
        raise CutplaceSniffError("content must contain data for format to be sniffed")
    _log.debug("found longest segment starting in row %d lasting for %d rows having %d columns",
        rowIndexWhereLongestSegmentStarts, longestSegmentRowCount, longestSegmentColumnCount)

    assert rowIndexWhereLongestSegmentStarts is not None
    _log.debug("skip %d rows until longest segment starts", rowIndexWhereLongestSegmentStarts)
    readable.seek(0)
    reader = createReader(readable)
    rowIndex = 0
    location = tools.InputLocation(readable)
    while rowIndex < rowIndexWhereLongestSegmentStarts:
        reader.next()
        location.advanceLine()
        rowIndex += 1

    _log.info("analyze longest segment of rows with same column count")
    columnInfos = []
    for columnIndex in range(longestSegmentColumnCount):
        columnInfos.append(_ColumnSniffInfo(columnIndex, dataFormat))
    rowIndex = 0
    while rowIndex < longestSegmentRowCount:
        rowToAnalyze = reader.next()
        columnCountOfRowToAnalyze = len(rowToAnalyze)
        if columnCountOfRowToAnalyze != longestSegmentColumnCount:
            raise CutplaceSniffError("data must not change between sniffer passes, but row %d now has %d columns instead of %d" \
                % (rowIndex + 1, columnCountOfRowToAnalyze, longestSegmentColumnCount), location)
        for itemIndex in range(longestSegmentColumnCount):
            value = rowToAnalyze[itemIndex]
            columnInfos[itemIndex].process(value)
        location.advanceLine()
        rowIndex += 1

    for columnIndex in range(longestSegmentColumnCount):
        _log.debug("  %s" % columnInfos[columnIndex].asFieldFormat())

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
