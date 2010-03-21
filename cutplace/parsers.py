"""
Parsers to read tabular data from various input formats and yield each row as a Python array
containing the columns.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import csv
import data
import datetime
import decimal
import logging
import ods
import os
import Queue
import tempfile
import tools

AUTO = data.ANY
CR = "\r"
LF = "\n"
CRLF = CR + LF
_VALID_LINE_DELIMITERS = [AUTO, CR, CRLF, LF]

class CutplaceXlrdImportError(tools.CutplaceError):
    """
    Error raised if xlrd package to read Excel can not be imported.
    """
    
def delimitedReader(readable, dialect, encoding="ascii"):
    """Generator yielding the "readable" row by row using "dialect"."""
    assert readable is not None
    assert dialect is not None
    assert encoding is not None
    
    parser = _DelimitedParser(readable, dialect, encoding)
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()

def fixedReader(readable, fieldLengths):
    """Generator yielding the "readable" row by row using "fieldLengths"."""
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

def _excelCellValue(cell, datemode):
    """
    The value of `cell` as text taking into account the way excel encodes dates and times.

    Numeric Excel types (Currency,  Fractional, Number, Percent, Scientific) simply yield the decimal number without any special formatting.
    
    Dates result in a text using the format "YYYY-MM-DD", times in a text using the format "hh:mm:ss".
    
    Boolean yields "0" or "1".
    
    Formulas are evaluated and yield the respective result.
    """
    assert cell is not None

    # Just import without sanitizing the error message.
    # If we got that far, the import should have worked already.
    import xlrd

    if cell.ctype == xlrd.XL_CELL_DATE:
        cellTuple = xlrd.xldate_as_tuple(cell.value, datemode)
        assert len(cellTuple) == 6, "cellTuple=%r" % cellTuple
        if cellTuple[:3] == (0, 0, 0):
            timeTuple = cellTuple[3:]
            result = unicode(str(datetime.time(*timeTuple)), "ascii")
        else:
            result = unicode(str(datetime.datetime(*cellTuple)), "ascii")
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        defaultErrorText = xlrd.error_text_from_code[0x2a] # same as "#N/A!"
        errorCode = cell.value
        result = unicode(xlrd.error_text_from_code.get(errorCode, defaultErrorText), "ascii")
    elif isinstance(cell.value, unicode):
        result = cell.value
    else:
        result = unicode(str(cell.value), "ascii")
        if (cell.ctype == xlrd.XL_CELL_NUMBER) and (result.endswith(u".0")):
            result = result[: - 2]

    return result

def excelReader(readable, sheetIndex=1):
    """
    Generator yielding the Excel spreadsheet located in the workbook stored in `readable` at index `sheetIndex` row
    by row.
    """
    assert readable is not None
    assert sheetIndex is not None
    assert sheetIndex >= 1
    
    try:
        import xlrd
    except ImportError:
        raise CutplaceXlrdImportError("to read Excel data the xlrd package must be installed, see <http://pypi.python.org/pypi/xlrd> for more information")
        
    contents = readable.read()
    workbook = xlrd.open_workbook(file_contents=contents)
    datemode = workbook.datemode
    sheet = workbook.sheet_by_index(sheetIndex - 1)
    for y in range(sheet.nrows):
        row = []
        for x in range(sheet.ncols):
            row.append(_excelCellValue(sheet.cell(y, x), datemode))
        yield row

def odsReader(readable, sheetIndex=1):
    """
    Generator yielding the Open Document spreadsheet stored in `readable`.
    """
    assert readable is not None
    assert sheetIndex is not None
    assert sheetIndex >= 1

    rowQueue = Queue.Queue()
    contentXmlReadable = ods.odsContent(readable)
    try:
        producer = ods.ProducerThread(contentXmlReadable, rowQueue, sheetIndex)
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
        
    def __str__(self):
        result = "(" + tools.valueOr("%d" % (self.lineNumber + 1), "?")
        if self.columnNumberInLine is not None:
            result += ";%d" % self.columnNumberInLine
        if self.itemNumberInLine is not None:
            result += "@%d" % (self.itemNumberInLine + 1)
        result += "): %s" % self.message
        return result
            
class _DelimitedParser(object):
    """Parser for data where items are separated by delimiters."""
    def __init__(self, readable, dialect, encoding="ascii"):
        assert readable is not None
        assert dialect is not None
        assert encoding is not None
        assert dialect.lineDelimiter is not None
        assert dialect.itemDelimiter is not None

        self._log = logging.getLogger("cutplace.parsers")

        # Automatically set line and item delimiter.
        # TODO: Use a more intelligent logic. Csv.Sniffer would be nice,
        # but not all test cases work with it.
        if (dialect.lineDelimiter == AUTO) or (dialect.itemDelimiter == AUTO):
            oldPosition = readable.tell()
            sniffedText = readable.read(16384)
            readable.seek(oldPosition)
        if dialect.lineDelimiter == AUTO:
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
            self._log.debug(" detected line delimiter: %r" % actualLineDelimiter)
        else:
            actualLineDelimiter = dialect.lineDelimiter
        if dialect.itemDelimiter == AUTO:
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
                self._log.debug(" detected item delimiter: %r" % actualItemDelimiter)
        else:
            actualItemDelimiter = dialect.itemDelimiter
        
        self.readable = readable
        self.lineDelimiter = actualLineDelimiter
        self.itemDelimiter = actualItemDelimiter
        self.quoteChar = dialect.quoteChar
        self.escapeChar = dialect.escapeChar
        self.blanksAroundItemDelimiter = dialect.blanksAroundItemDelimiter

        self.item = None

        # FIXME: Read delimited items without holding the whole file into memory.
        self.rows = []
        # HACK: Convert delimiters using `str()` because `csv.reader()` cannot handle Unicode strings,
        # thus u"," becomes "," which can be processed.
        reader = tools.UnicodeCsvReader(readable, delimiter=str(self.itemDelimiter), lineterminator=str(self.lineDelimiter),
                              quotechar=str(self.quoteChar), doublequote=(self.quoteChar == self.escapeChar), encoding=encoding)
        for row in reader:
            # TODO: Convert all items in row to Unicode.
            self.rows.append(row)
        self.rowCount = len(self.rows)
        self.itemNumber = 0
        if self.rowCount:
            self.atEndOfFile = False
            self.atEndOfLine = False
            self.lineNumber = 1
            # Attempt to read the first item.
            self.advance()
        else:
            # Handle empty `readable`.
            self.atEndOfFile = True
            self.atEndOfLine = True
            self.lineNumber = 0

    def advance(self):
        """
        Advance one item and make it available in `self.item`.
        """
        assert not self.atEndOfFile

        self.itemNumber += 1
        if self.itemNumber - 1 >= len(self.rows[self.lineNumber - 1]):
             self.itemNumber = 1
             self.lineNumber += 1
        if self.lineNumber <= len(self.rows):
            row = self.rows[self.lineNumber - 1]
            if len(row):
                self.item = row[self.itemNumber - 1]
            else:
                # Represent empty line as `None`.
                self.item = None
            self.atEndOfLine = (self.itemNumber >= len(row))
        else:
            self.item = None
            self.atEndOfFile = True
        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug("(%d:%d) %r [%d;%d]" % (self.lineNumber, self.itemNumber, self.item, self.atEndOfLine, self.atEndOfFile))

class _FixedParser(object):
    def __init__(self, readable, fieldLengths):
        assert readable is not None
        assert fieldLengths is not None
        assert len(fieldLengths) > 0
        
        self.readable = readable
        self.fieldLengths = fieldLengths
        # TODO: Obtain name of file to parse, if there is one.
        self.fileName = None
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
        # FIXME: Convert item to Unicode.
        if (self.item == "") and (self.itemNumberInRow == 0):
            self.item = None
            self.atEndOfLine = True
            self.atEndOfFile = True
        else: 
            actualLength = len(self.item)
            if actualLength != expectedLength:
                self._raiseSyntaxError("item must have %d characters but data already end after %d yielding: %r" % (expectedLength, actualLength, self.item))
            self.columnNumberInRow += actualLength
            if self.itemNumberInRow == len(self.fieldLengths) - 1:
                self.atEndOfLine = True
