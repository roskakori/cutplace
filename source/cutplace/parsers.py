"""
Parsers to read tabular data from various input formats and yield each row as a Python array
containing the columns.
"""
import csv
import data
import logging
import ods
import os
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
    
def parserReader(parser):
    """Generator yielding the readable of parser row by row."""
    assert parser is not None
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()

def delimitedReader(readable, dialect):
    """Generator yielding the "readable" row by row using "dialect"."""
    assert readable is not None
    assert dialect is not None
    
    parser = DelimitedParser(readable, dialect)
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
    
    parser = FixedParser(readable, fieldLengths)
    # parserReader(parser)
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()

def excelReader(readable, sheetIndex=0):
    """Generator yielding the "readable" row by row using "fieldLengths"."""
    assert readable is not None
    assert sheetIndex is not None
    
    parser = ExcelParser(readable, sheetIndex)
    # parserReader(parser)
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()

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
            
class DelimitedParser(object):
    """Parser for data where items are separated by delimiters."""
    def __init__(self, readable, dialect):
        assert readable is not None
        assert dialect is not None
        assert dialect.lineDelimiter is not None
        assert dialect.itemDelimiter is not None

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
        else:
            actualLineDelimiter = dialect.lineDelimiter
        if dialect.itemDelimiter == AUTO:
            commaCount = sniffedText.count(",")
            semicolonCount = sniffedText.count(";")
            if commaCount > semicolonCount:
                actualItemDelimiter = ","
            else:
                actualItemDelimiter = ";"
        else:
            actualItemDelimiter = dialect.itemDelimiter
        
        self.readable = readable
        self.lineDelimiter = actualLineDelimiter
        self.itemDelimiter = actualItemDelimiter
        self.quoteChar = dialect.quoteChar
        self.escapeChar = dialect.escapeChar
        self.blanksAroundItemDelimiter = dialect.blanksAroundItemDelimiter

        self._log = logging.getLogger("cutplace.parsers")
        self.item = None

        # FIXME: Read delimited items without holding the whole file into memory.
        self.rows = []
        for row in csv.reader(readable):
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
        
class OdsParser(DelimitedParser):
    """Parser for Open Document Spreadsheets (ODS)."""
    def __init__(self, readable):
        # Convert ODS to CSV.
        (csvTempFd, self.csvTempFilePath) = tempfile.mkstemp(".csv", "cutplace-")
        os.close(csvTempFd)
        ods.toCsv(readable, self.csvTempFilePath)
        
        excelDialect = DelimitedDialect(AUTO, ",")
        excelDialect.quoteChar = "\""

        # Now act as DelimitedParser for the derived CSV.
        self.csvTempFile = open(self.csvTempFilePath, "rb")
        super(OdsParser, self).__init__(self.csvTempFile, excelDialect)
    
    def _removeCsvTempTargetFile(self):
        self.csvTempFile.close()
        os.remove(self.csvTempFilePath)

    def advance(self):
        try:
            super(OdsParser, self).advance()
            if self.atEndOfFile:
                self._removeCsvTempTargetFile()
        except:
            self._removeCsvTempTargetFile

class FixedParser(object):
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

class ExcelParser(object):
    def __init__(self, readable, sheetIndex=0):
        assert readable is not None
        assert sheetIndex is not None
        
        try:
            import xlrd
        except ImportError:
            raise CutplaceXlrdImportError("to read Excel data the xlrd package must be installed, see <http://pypi.python.org/pypi/xlrd> for more information")
        
        contents = readable.read()
        self.workbook = xlrd.open_workbook(file_contents=contents)
        self.sheet = self.workbook.sheet_by_index(sheetIndex)
        # TODO: Obtain name of file to parse, if there is one.
        self.fileName = None
        self.itemNumberInRow = - 1
        self.rowNumber = 0
        self.atEndOfLine = False
        self.atEndOfFile = False
        self.item = None
        self._log = logging.getLogger("cutplace.parsers")

        self.advance()
        
    def advance(self):
        assert not self.atEndOfFile
        
        if self.atEndOfLine:
            self.itemNumberInRow = 0
            self.columnNumberInRow = 0
            self.rowNumber += 1
            self.atEndOfLine = False
        else:
            self.itemNumberInRow += 1

        if self.rowNumber >= self.sheet.nrows:
            # Last row reached.
            self.item = None
            self.atEndOfLine = True
            self.atEndOfFile = True
        else:
            if self._log.isEnabledFor(logging.DEBUG):
                self._log.debug("parse excel item at (%d:%d) of (%d:%d)"
                                % (self.rowNumber, self.itemNumberInRow, self.sheet.nrows, self.sheet.ncols))
            self.item = self.sheet.cell_value(self.rowNumber - 1, self.itemNumberInRow)
            if self.itemNumberInRow + 1 == self.sheet.ncols:
                self.atEndOfLine = True
