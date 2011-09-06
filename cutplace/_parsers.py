"""
Parsers to read tabular data from various input formats and yield each row as a Python array
containing the columns.
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
import csv
import datetime
import logging
import Queue
import threading

import data
import sniff
import tools
import _ods
import _tools

AUTO = data.ANY
CR = "\r"
LF = "\n"
CRLF = CR + LF
_VALID_LINE_DELIMITERS = [AUTO, CR, CRLF, LF]


class CutplaceXlrdImportError(tools.CutplaceError):
    """
    Error raised if ``xlrd`` package to read Excel needs to be installed.
    """


def _createRowQueue():
    """
    A queue to be used for consumer/producer readers, ensuring that memory usage is kept at bay even when
    reading is much faster than validating.
    """
    return Queue.Queue(3)


class _AbstractRowProducerThread(threading.Thread):
    """
    Thread to produce the contents of a row reader to a queue where a consumer can get it.

    Consumers should call ``Queue.get()`` until it returns ``None``. Possible exceptions raised
    in the background during `run()` are raised again when calling `join()` so no special means
    are necessary for the consumer to handle exceptions in the producer thread.
    """
    def __init__(self, readable, targetQueue):
        assert readable is not None
        assert targetQueue is not None
        super(_AbstractRowProducerThread, self).__init__()
        self.readable = readable
        self._targetQueue = targetQueue
        self._error = None

    def reader(self):
        """
        Reader to yield ``readable`` row by row.
        """
        raise NotImplementedError(u'reader() must be implemented')

    def run(self):
        try:
            for row in self.reader():
                self._targetQueue.put(row)
        except Exception, error:
            # Remember error information to raise it later during `join()`.
            self._error = error
        finally:
            # The last row always is a `None` to mark the end.
            self._targetQueue.put(None)

    def join(self):
        super(_AbstractRowProducerThread, self).join()
        if self._error is not None:
            raise self._error


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
        assert len(cellTuple) == 6, u"cellTuple=%r" % cellTuple
        if cellTuple[:3] == (0, 0, 0):
            timeTuple = cellTuple[3:]
            result = unicode(datetime.time(*timeTuple))
        else:
            result = unicode(datetime.datetime(*cellTuple))
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        defaultErrorText = xlrd.error_text_from_code[0x2a]  # same as "#N/A!"
        errorCode = cell.value
        result = unicode(xlrd.error_text_from_code.get(errorCode, defaultErrorText), "ascii")
    elif isinstance(cell.value, unicode):
        result = cell.value
    else:
        result = unicode(cell.value)
        if (cell.ctype == xlrd.XL_CELL_NUMBER) and (result.endswith(u".0")):
            result = result[:-2]

    return result


class _ExcelRowProducerThread(_AbstractRowProducerThread):
    def __init__(self, readable, targetQueue, sheetIndex=1):
        assert sheetIndex is not None
        assert sheetIndex >= 1
        super(_ExcelRowProducerThread, self).__init__(readable, targetQueue)
        self.sheetIndex = sheetIndex

    def reader(self):
        try:
            import xlrd
        except ImportError:
            raise CutplaceXlrdImportError(u"to read Excel data the xlrd package must be installed, see <http://pypi.python.org/pypi/xlrd> for more information")

        contents = self.readable.read()
        workbook = xlrd.open_workbook(file_contents=contents)
        datemode = workbook.datemode
        sheet = workbook.sheet_by_index(self.sheetIndex - 1)
        for y in range(sheet.nrows):
            row = []
            for x in range(sheet.ncols):
                row.append(_excelCellValue(sheet.cell(y, x), datemode))
            yield row


def delimitedReader(readable, dialect, encoding="ascii"):
    """
    Generator yielding the ``readable`` row by row using `DelimitedDialect` ``dialect`` and ``encoding``.
    """
    assert readable is not None
    assert dialect is not None
    assert encoding is not None

    rowQueue = _createRowQueue()
    producer = _DelimitedRowProducerThread(readable, rowQueue, dialect, encoding)
    producer.start()
    hasRow = True
    while hasRow:
        row = rowQueue.get()
        if row is not None:
            yield row
        else:
            hasRow = False
    producer.join()


def excelReader(readable, sheetIndex=1):
    """
    Generator yielding the Excel spreadsheet located in the workbook stored in ``readable`` at index
    ``sheetIndex`` row by row.
    """
    assert readable is not None
    assert sheetIndex is not None
    assert sheetIndex >= 1

    rowQueue = _createRowQueue()
    producer = _ExcelRowProducerThread(readable, rowQueue, sheetIndex)
    producer.start()
    hasRow = True
    while hasRow:
        row = rowQueue.get()
        if row is not None:
            yield row
        else:
            hasRow = False
    producer.join()


def odsReader(readable, sheetIndex=1):
    """
    Generator yielding the Open Document spreadsheet stored in ``readable`` in sheet number ``sheetIndex``
    starting with 1.
    """
    assert readable is not None
    assert sheetIndex is not None
    assert sheetIndex >= 1

    rowQueue = _createRowQueue()
    contentXmlReadable = _ods.odsContent(readable)
    try:
        producer = _ods.ProducerThread(contentXmlReadable, rowQueue, sheetIndex)
        producer.start()
        hasRow = True
        while hasRow:
            row = rowQueue.get()
            if row is not None:
                yield row
            else:
                hasRow = False
    finally:
        contentXmlReadable.close()
    producer.join()


class DelimitedDialect(object):
    def __init__(self, lineDelimiter=AUTO, itemDelimiter=AUTO):
        assert lineDelimiter is not None
        assert lineDelimiter in  _VALID_LINE_DELIMITERS
        assert itemDelimiter is not None
        # assert len(itemDelimiter) == 1

        self.lineDelimiter = lineDelimiter
        self.itemDelimiter = itemDelimiter
        self.quoteChar = None
        self.escapeChar = None
        self.blanksAroundItemDelimiter = " \t"
        # FIXME: Add setter for quoteChar to validate that len == 1 and quoteChar != line- or itemDelimiter.

    def asCsvDialect(self):
        """
        Represent dialect as csv.Dialect.
        """
        result = csv.Dialect()
        result.lineterminator = self.lineDelimiter
        result.delimiter = self.itemDelimiter
        result.quotechar = self.quoteChar
        result.doublequote = (self.escapeChar == self.quoteChar)
        if not result.doublequote:
            result.escapechar = self.escapeChar
        result.skipinitialspace = (self.blanksAroundItemDelimiter)

        return result


class ParserSyntaxError(tools.CutplaceError):
    """
    Syntax error detected while parsing the data.
    """
    def __init__(self, message, lineNumber=None, itemNumberInLine=None, columnNumberInLine=None):
        super(Exception, self).__init__(message)
        assert lineNumber is not None
        assert lineNumber >= 0
        assert itemNumberInLine is not None
        assert itemNumberInLine >= 0
        assert columnNumberInLine is not None
        assert columnNumberInLine >= 0

        self.message = message
        self.lineNumber = lineNumber
        self.itemNumberInLine = itemNumberInLine
        self.columnNumberInLine = columnNumberInLine

    def __unicode__(self):
        result = u"(" + _tools.valueOr(u"%d" % (self.lineNumber + 1), u"?")
        if self.columnNumberInLine is not None:
            result += u";%d" % self.columnNumberInLine
        if self.itemNumberInLine is not None:
            result += u"@%d" % (self.itemNumberInLine + 1)
        result += u"): %s" % self.message
        return result

    def __str__(self):
        unicode(self).encode('utf-8')

    def __repr__(self):
        return "ParserSyntaxError(%s)" % self.__str__()


class _DelimitedRowProducerThread(_AbstractRowProducerThread):
    def __init__(self, readable, targetQueue, dialect, encoding="ascii"):
        assert dialect is not None
        assert dialect.lineDelimiter is not None
        assert dialect.itemDelimiter is not None
        assert encoding is not None
        super(_DelimitedRowProducerThread, self).__init__(readable, targetQueue)

        self._log = logging.getLogger("cutplace.parsers")

        dialectKeyowrds = {
            sniff._ENCODING: encoding,
            sniff._ESCAPE_CHARACTER: dialect.escapeChar,
            sniff._ITEM_DELIMITER: dialect.itemDelimiter,
            sniff._LINE_DELIMITER: dialect.lineDelimiter,
            sniff._QUOTE_CHARACTER: dialect.quoteChar
        }
        delimitedOptions = sniff.delimitedOptions(readable, **dialectKeyowrds)

        self.readable = readable
        self.encoding = encoding
        self.lineDelimiter = delimitedOptions[sniff._LINE_DELIMITER]
        self.itemDelimiter = delimitedOptions[sniff._ITEM_DELIMITER]
        self.quoteChar = delimitedOptions[sniff._QUOTE_CHARACTER]
        self.escapeChar = delimitedOptions[sniff._ESCAPE_CHARACTER]
        self.blanksAroundItemDelimiter = dialect.blanksAroundItemDelimiter

    def reader(self):
        rowReader = _tools.UnicodeCsvReader(self.readable, delimiter=str(self.itemDelimiter),
            lineterminator=str(self.lineDelimiter), quotechar=str(self.quoteChar),
            doublequote=(self.quoteChar == self.escapeChar), encoding=self.encoding)
        hasData = False
        hasDelayedEmptyRow = False
        for row in rowReader:
            if not hasData and not hasDelayedEmptyRow and not row:
                # if the first row is an empty row, suppress it unless further rows are coming. This ensures
                # that an empty data set results in an empty list of rows.
                hasDelayedEmptyRow = True
            else:
                if hasDelayedEmptyRow:
                    hasDelayedEmptyRow = False
                    hasData = True
                    yield []
                yield row


class _FixedParser(object):
    def __init__(self, readable, fieldLengths):
        assert readable is not None
        assert fieldLengths is not None
        assert len(fieldLengths) > 0

        self.readable = readable
        self.fieldLengths = fieldLengths
        self.itemNumberInRow = - 1
        self.columnNumberInRow = 0
        self.rowNumber = 0
        self.atEndOfLine = False
        self.atEndOfFile = False
        self.item = 0
        self.advance()

    def _raiseSyntaxError(self, message):
        assert message is not None
        raise ParserSyntaxError(message, self.rowNumber, self.itemNumberInRow, self.columnNumberInRow)

    def advance(self):
        assert not self.atEndOfFile

        if self.atEndOfLine:
            self.itemNumberInRow = 0
            self.columnNumberInRow = 0
            self.rowNumber += 1
            self.atEndOfLine = False
        else:
            self.itemNumberInRow += 1
        expectedLength = self.fieldLengths[self.itemNumberInRow]
        self.item = self.readable.read(expectedLength)
        if not isinstance(self.item, unicode):
            raise UnicodeEncodeError(u"filelike object for fixed data set must be opened using codecs.open() instead of open()")
        if (self.item == "") and (self.itemNumberInRow == 0):
            self.item = None
            self.atEndOfLine = True
            self.atEndOfFile = True
        else:
            actualLength = len(self.item)
            if actualLength != expectedLength:
                self._raiseSyntaxError(
                    u"item must have %d characters but data already end after %d yielding: %r"
                    % (expectedLength, actualLength, self.item)
                )
            self.columnNumberInRow += actualLength
            if self.itemNumberInRow == len(self.fieldLengths) - 1:
                self.atEndOfLine = True


class _FixedRowProducerThread(_AbstractRowProducerThread):
    def __init__(self, readable, targetQueue, fieldLengths):
        assert fieldLengths
        assert len(fieldLengths) > 0
        super(_FixedRowProducerThread, self).__init__(readable, targetQueue)
        self.fieldLengths = fieldLengths

    def reader(self):
        parser = _FixedParser(self.readable, self.fieldLengths)
        columns = []
        while not parser.atEndOfFile:
            if parser.item is not None:
                columns.append(parser.item)
            if parser.atEndOfLine:
                yield columns
                columns = []
            parser.advance()


def fixedReader(readable, fieldLengths):
    """
    Generator yielding the ``readable`` row by row using ``fieldLengths``.
    """
    assert readable is not None
    assert fieldLengths
    assert len(fieldLengths) > 0

    parser = _FixedParser(readable, fieldLengths)
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()
