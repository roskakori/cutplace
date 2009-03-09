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
            
class DelimitedParser(object):
    """Parser for data where items are separated by delimiters."""
    def __init__(self, readable, dialect):
        assert readable is not None
        assert dialect is not None
        assert dialect.lineDelimiter is not None
        assert dialect.itemDelimiter is not None

        self.readable = readable
        self.lineDelimiter = dialect.lineDelimiter
        self.itemDelimiter = dialect.itemDelimiter
        self.quoteChar = dialect.quoteChar
        self.escapeChar = dialect.escapeChar
        self.blanksAroundItemDelimiter = dialect.blanksAroundItemDelimiter

        self.log = logging.getLogger("cutplace")
        self.atEndOfLine = False
        self.atEndOfFile = False
        self.item = None
        self.columnNumber = 0
        self.lineNumber = 0
        self.unreadChars = ""
        
        # Attempt to read the first item.
        self.advance()
        
    def _unread(self, charsToUnread):
        assert charsToUnread is not None
        assert charsToUnread, "characters to unread must be specified"
        self.unreadChars += charsToUnread
        self.columnNumber -= len(charsToUnread)
        assert self.columnNumber >= 0, "column=%d" %(self.columnNumber)
                
    def _read(self):
        if self.unreadChars:
            result = self.unreadChars[0]
            self.unreadChars = self.unreadChars[1:]
        else:
            result = self.readable.read(1)
        if result:
            self.columnNumber += 1
        return result
    
    def _possiblyAdvanceLine(self):
        if self.atEndOfLine:
            self.atEndOfLine = False
            self.lineNumber += 1
    
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

        self.item = None
        quoted = False

        self._possiblySkipSpace()
        
        firstChar = self._read()
        
        # Skip blanks before actual item starts.
        if self.blanksAroundItemDelimiter:
            while firstChar and (firstChar in self.blanksAroundItemDelimiter):
                firstChar = self._read()

        if not firstChar:
            # End of file reached.
            self.atEndOfFile = True
            self.atEndOfLine = True
            self.item = None
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
                else:
                    self.atEndOfLine = True
                    atEndOfItem = True
            self.item = item
            
            self._possiblySkipSpace()
            tail = self._read()
            if not tail or (tail == self.itemDelimiter):
                pass
            elif tail != self.lineDelimiter:
                raise DelimitedSyntaxError("data item must be followed by line feed or item delimiter, but found: \"" + tail + "\"")
            
            
        
        
        
    
     
