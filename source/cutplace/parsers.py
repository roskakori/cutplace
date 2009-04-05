"""Parsers for data files."""
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
        self.atEndOfFile = False
        self.item = None
        self.unreadChars = ""

        # Reset all attributes related to position.
        self.atEndOfLine = True
        self.lineNumber = - 1
        self._possiblyAdvanceLine()
        
        # Attempt to read the first item.
        self.advance()

    def _unread(self, charsToUnread):
        assert charsToUnread is not None
        assert charsToUnread, "characters to unread must be specified"
        if (self._log.isEnabledFor(logging.DEBUG)):
            self._log.debug("unread: %r" % charsToUnread)
        self.unreadChars += charsToUnread
        self.columnNumber -= len(charsToUnread)
        assert self.columnNumber >= 0, "column=%d" % (self.columnNumber)
                
    def _read(self):
        if self.unreadChars:
            result = self.unreadChars[0]
            self.unreadChars = self.unreadChars[1:]
        else:
            result = self.readable.read(1)
        if result:
            self.columnNumber += 1
        if (self._log.isEnabledFor(logging.DEBUG)):
            self._log.debug("read: %r" % result)
        return result
    
    def _raiseSyntaxError(self, message):
        """Raise syntax error at the current position."""
        raise ParserSyntaxError(message, self.lineNumber, self.itemNumber, self.columnNumber)

    def _possiblyAdvanceLine(self):
        if self.atEndOfLine:
            self.atEndOfLine = False
            self.lineNumber += 1
            self.itemNumber = 0
            self.columnNumber = 0
    
    def _possiblySkipSpace(self):
        if self.blanksAroundItemDelimiter:
            possibleBlank = self._read()
            while possibleBlank and (possibleBlank in self.blanksAroundItemDelimiter):
                possibleBlank = self._read()
            if possibleBlank:
                self._unread(possibleBlank)
            
    def advance(self):
        """Advance one item."""
        # FIXME: Support escaped quotes.
        assert not self.atEndOfFile
        assert self.lineDelimiter != AUTO

        self.item = None
        quoted = False
        stripLineDelimiter = False

        self._possiblyAdvanceLine()
        self._possiblySkipSpace()
        
        firstChar = self._read()
        if not firstChar:
            # End of file reached.
            self.atEndOfFile = True
            self.atEndOfLine = True
        else:
            atEndOfItem = False

            # Check if the item is quoted.
            if firstChar == self.quoteChar:
                endOfItemChar = firstChar
                item = ""
                quoted = True
            elif firstChar == self.itemDelimiter:
                self._unread(firstChar)
                item = ""
                atEndOfItem = True
            elif firstChar == self.lineDelimiter:
                # Note: CRLF will be detected in the while loop below.
                item = firstChar
                atEndOfItem = True
                stripLineDelimiter = True
            else:
                endOfItemChar = self.itemDelimiter
                item = firstChar

            # Read actual item content.
            while not atEndOfItem:
                nextChar = self._read()
                if nextChar:
                    if nextChar == endOfItemChar:
                        atEndOfItem = True
                        if not quoted:
                            self._unread(nextChar)
                    else:
                        item += nextChar
                        if not quoted and item.endswith(self.lineDelimiter):
                            self._log.debug("detected line delimiter: %r" % self.lineDelimiter)
                            stripLineDelimiter = True
                            atEndOfItem = True
                else:
                    if quoted:
                        # TODO: Use start of item as position to report for error.
                        self._raiseSyntaxError("item must be terminated with quote (%s) before data end" % (self.quoteChar))
                    self.atEndOfLine = True
                    atEndOfItem = True
                    # Handle empty line with line delimiter at end of file
                    if item == self.lineDelimiter:
                        stripLineDelimiter = True

            # Remove line delimiter from unquoted items at end of line.
            if stripLineDelimiter:
                self._log.debug("stripped linefeed after unquoted item, remainder: %r" % item)
                item = item[: - len(self.lineDelimiter)]
                self.atEndOfLine = True

            # Ensure that item is followed by either an item separator, a line separator or the end of data is reached. 
            if not self.atEndOfLine:
                self._possiblySkipSpace()
                nextChar = self._read()
                if not nextChar:
                    self.atEndOfLine = True
                elif nextChar != self.itemDelimiter:
                    tail = nextChar
                    while nextChar and (tail != self.lineDelimiter) and (self.lineDelimiter.startswith(tail)):
                        nextChar = self._read()
                        tail += nextChar
                    if tail == self.lineDelimiter:
                        self.atEndOfLine = True
                    else:
                        self._raiseSyntaxError(\
                               "data item must be followed by item delimiter (%r) or line delimiter (%r), but found: %r" \
                                % (self.itemDelimiter, self.lineDelimiter, tail))

            self.item = item
            if self.item is not None:
                self.itemNumber += 1

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
