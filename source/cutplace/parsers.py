"""Parsers for data files."""
import logging
import string

AUTO = "?"
CR = "\r"
LF = "\n"
CRLF = CR + LF
_VALID_LINE_DELIMITERS = [AUTO, CR, CRLF, LF]
    
class DelimitedDialect(object):
    def __init__(self, lineDelimter=AUTO, itemDelimiter=AUTO):
        assert lineDelimter is not None
        assert lineDelimter in  _VALID_LINE_DELIMITERS
        assert itemDelimiter is not None
        assert len(itemDelimiter) == 1
        
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

        self.readable = readable
        # FIXME: Detect first line feed in case of AUTO
        self.lineDelimiter = dialect.lineDelimiter
        self.itemDelimiter = dialect.itemDelimiter
        self.quoteChar = dialect.quoteChar
        self.escapeChar = dialect.escapeChar
        self.blanksAroundItemDelimiter = dialect.blanksAroundItemDelimiter

        self.log = logging.getLogger("cutplace")
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
            
    def _matchingEndOfLine(self, text):
        """Yield in which end of line sequence text ends, or None if no sequence matches."""
        result = None
        eolIndex = 0
        while (result is None) and (eolIndex < len(self.lineDelimiter)):
            delimiter = self.lineDelimiter(eolIndex)
            if text.endswith(delimiter):
                result = delimiter
            else:
                eolIndex += 1
        return result
             
    def advance(self):
        """Advance one item."""
        assert not self.atEndOfFile
        assert self.lineDelimiter != AUTO

        self.item = None
        quoted = False

        self._possiblyAdvanceLine()
        self._possiblySkipSpace()
        
        firstChar = self._read()
        if not firstChar:
            # End of file reached.
            self.atEndOfFile = True
            self.atEndOfLine = True
        else:
            # Check if the item is quoted.
            if firstChar == self.quoteChar:
                endOfItemChar = firstChar
                item = ""
                quoted = True
            else:
                endOfItemChar = self.itemDelimiter
                item = firstChar

            # Read actual item content.
            atEndOfItem = False
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
                            self.log.debug("detected linefeed")
                            atEndOfItem = True
                else:
                    self.atEndOfLine = True
                    atEndOfItem = True
            # Detect and of line
            if not quoted and item.endswith(self.lineDelimiter):
                    self.log.debug("trimmed linefeed from unquoted item, remainder: \"%s\"" % (item))
                    item = item[: - len(self.lineDelimiter)]
                    self.atEndOfLine = True
                    self._unread(self.lineDelimiter)

            self.item = item
            if self.item is not None:
                self.itemNumber += 1
                
            self._possiblySkipSpace()
            tail = self._read()
            if not tail or (tail == self.itemDelimiter):
                pass
            elif tail != self.lineDelimiter:
                self._raiseSyntaxError("data item must be followed by line feed or item delimiter, but found: \"" + tail + "\"")
