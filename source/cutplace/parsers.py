"""Parsers for data files."""
import data
import logging
import string

AUTO = data.ANY
CR = "\r"
LF = "\n"
CRLF = CR + LF
_VALID_LINE_DELIMITERS = [AUTO, CR, CRLF, LF]

def delimitedReader(readable, dialect):
    """Generator yielding the "readable" line by line using "dialect"."""
    parser = DelimitedParser(readable, dialect)
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()

def parserReader(parser):
    """Generator yielding the "readable" line by line using "dialect"."""
    assert parser is not None
    columns = []
    while not parser.atEndOfFile:
        if parser.item is not None:
            columns.append(parser.item)
        if parser.atEndOfLine:
            yield columns
            columns = []
        parser.advance()


class DelimitedDialect(object):
    def __init__(self, lineDelimter=AUTO, itemDelimiter=AUTO):
        assert lineDelimter is not None
        assert lineDelimter in  _VALID_LINE_DELIMITERS
        assert itemDelimiter is not None
        # assert len(itemDelimiter) == 1
        
        self.lineDelimiter = itemDelimiter
        self.itemDelimiter = itemDelimiter
        self.quoteChar = None
        self.escapeChar = None
        self.blanksAroundItemDelimiter = " \t"
        # FIXME: Add setter for quoteChar to validate that len == 1 and quoteChar != line- or itemDelimiter.

class DelimitedSyntaxError(Exception):
    """Error detecting while parsing delimited data."""
    def __init__(self, message, lineNumber, itemNumberInLine, columnNumberInLine):
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
        return "%d,%d,%d: %s" % (self.lineNumber, self.itemNumberInLine, self.columnNumberInLine, str(self.message))
            
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
        raise DelimitedSyntaxError(message, self.lineNumber, self.itemNumber, self.columnNumber)

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
                        self._raiseSyntaxError("item must be terminated with quote (%s) before file ends" % (self.quoteChar))
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
