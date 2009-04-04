"""Data formats."""
import codecs
import logging
import string
import tools

ANY = "any"
CR = "cr"
LF = "lf"
CRLF = "crlf"
_VALID_LINE_DELIMITER_TEXTS = [ANY, CR, CRLF, LF]
_VALID_LINE_DELIMITERS = [ANY, "\r", "\r\n", "\n"]
_VALID_QUOTE_CHARACTERS = ["\"", "\'"]
_VALID_ESCAPE_CHARACTERS = ["\"", "\\"]

FORMAT_CSV = "csv"
FORMAT_DELIMITED = "delimited"
FORMAT_FIXED = "fixed"
FORMAT_ODS = "ods"

KEY_ALLOWED_CHARACTERS = "allowed characters"
KEY_ENCODING = "encoding"
KEY_FORMAT = "format"
KEY_ITEM_DELIMITER = "item delimiter"
KEY_LINE_DELIMITER = "line delimiter"
KEY_QUOTE_CHARACTER = "quote character"
KEY_ESCAPE_CHARACTER = "escape character"

# TODO: Add KEY_DECIMAL_SEPARATOR = "decimalSeparator"
# TODO: Add KEY_THOUSANDS_SEPARATOR = "thousandsSeparator"

def createDataFormat(name):
    """Factory function to create the specified data format."""
    assert name is not None
    actualName = name.lower()
    if actualName == FORMAT_CSV:
        result = CsvDataFormat()
    elif actualName == FORMAT_DELIMITED:
        result = DelimitedDataFormat()
    elif actualName == FORMAT_FIXED:
        result = FixedDataFormat()
    elif actualName == FORMAT_ODS:
        result = OdsDataFormat()
    else:
        raise DataFormatSyntaxError("data format is %r but must be on of: %r" % (name, [FORMAT_CSV, FORMAT_DELIMITED, FORMAT_FIXED]))
    return result

def _isKey(possibleKey, keyToCompareWith):
    """True if possibleKey and keyToCompareWith match, ignoring case and blanks between words.""" 
    possibleKeyWords = possibleKey.lower().split()
    keyToCompareWithWords = keyToCompareWith.lower().split()
    return possibleKeyWords == keyToCompareWithWords

def isFormatKey(key):
    """True if key matches KEY_FORMAT."""
    return _isKey(key, KEY_FORMAT)

class DataFormatValueError(tools.CutplaceError):
    pass

class DataFormatLookupError(tools.CutplaceError):
    pass

class DataFormatSyntaxError(tools.CutplaceError):
    pass

class AbstractDataFormat(object):
    """Abstract data format acting as base for other data formats."""
    def __init__(self):
        assert type
        self._encoding = None
        self._lineDelimiter = None
        self._allowedCharacters = None
    
    def getName(self):
        raise NotImplemented
    
    def getEncoding(self):
        return self._encoding
    
    def setEncoding(self, encoding):
        assert encoding
        self._encoding = codecs.lookup(encoding)
        
    def getLineDelimiter(self):
        return self._lineDelimiter
    
    def setLineDelimiter(self, lineDelimiter):
        assert lineDelimiter is not None
        
        try:
            lineDelimiterIndex = _VALID_LINE_DELIMITER_TEXTS.index(lineDelimiter.lower())
        except: # Why ValueError instead of LookupError?
            raise DataFormatLookupError("%s is %r but must be one of: %r" % (KEY_LINE_DELIMITER, lineDelimiter, _VALID_LINE_DELIMITER_TEXTS))
        self._lineDelimiter = _VALID_LINE_DELIMITERS[lineDelimiterIndex]
        
    def setAllowedCharacters(self, text):
        assert text
        ranges = text.split(",")
        for range in ranges:
            # TODO: Parse character range.
            pass 
    
    def isAllowedCharacter(self, character):
        """Return True if character is allowed."""
        assert character is not None
        assert len(character) == 1
        
        # TODO: Check characters ranges.
        return True

    def set(self, key, value):
        assert key is not None
        assert value is not None
        
        lowerKey = key.lower()
        if _isKey(key, KEY_ALLOWED_CHARACTERS):
            self.setAllowedCharacters(value)
        elif _isKey(key, KEY_ENCODING):
            self.setEncoding(value)
        elif _isKey(key, KEY_LINE_DELIMITER):
            self.setLineDelimiter(value)
        else:
            raise DataFormatLookupError("unknown data format option: %r" % key)
    
class DelimitedDataFormat(AbstractDataFormat):
    """Data format for delimited data such as CSV."""
    def __init__(self, lineDelimiter=ANY, itemDelimiter=ANY):
        assert lineDelimiter is not None
        assert lineDelimiter in  _VALID_LINE_DELIMITERS
        assert (itemDelimiter == ANY) or (len(itemDelimiter) == 1)
        
        super(AbstractDataFormat, self).__init__()
        
        self.setLineDelimiter(lineDelimiter)
        self.setItemDelimiter(itemDelimiter)
        self._quoteCharacter = None
        self._escapeCharacter = None
        self._blanksAroundItemDelimiter = " \t"
        
    def getName(self):
        return FORMAT_DELIMITED

    def getItemDelimiter(self):
        return self._itemDelimiter
    
    def setItemDelimiter(self, itemDelimiter):
        assert itemDelimiter is not None
        assert (itemDelimiter == ANY) or (len(itemDelimiter) == 1)
        self._itemDelimiter = itemDelimiter

    def getQuoteCharacter(self):
        return self._quoteCharacter
    
    def setQuoteCharatcer(self, quoteCharacter):
        assert quoteCharacter is not None
        if not quoteCharacter in _VALID_QUOTE_CHARACTERS:
            raise DataFormatValueError("quote character is %r must be on of: %r" % _VALID_QUOTE_CHARACTERS)
        self._quoteCharacter = quoteCharacter
    
    def getEscapeCharacter(self):
        return self._escapeCharacter
    
    def setEscapeCharacter(self, escapeCharacter):
        assert escapeCharacter is not None
        if not escapeCharacter in _VALID_ESCAPE_CHARACTERS:
            raise DataFormatValueError("escape character is %r but must be on of: %r" % (escapeCharacter, _VALID_ESCAPE_CHARACTERS))
        self._escapeCharacter = escapeCharacter

    def set(self, key, value):
        assert key is not None
        assert value is not None
        
        lowerKey = key.lower()
        if _isKey(key, KEY_ESCAPE_CHARACTER):
            self.setEscapeCharacter(value)
        elif _isKey(key, KEY_ITEM_DELIMITER):
            self.setItemDelimiter(value)
        elif _isKey(key, KEY_QUOTE_CHARACTER):
            self.setQuoteCharatcer(value)
        else:
            super(DelimitedDataFormat, self).set(key, value)
    
class CsvDataFormat(DelimitedDataFormat):
    """Data format for comma separated values (CSV)."""
    def __init__(self):
        super(DelimitedDataFormat, self).__init__()
        self.setLineDelimiter(ANY)
        self.setItemDelimiter(ANY)
        self.setQuoteCharatcer("\"")
        self.setEscapeCharacter("\"")

    def getName(self):
        return FORMAT_CSV
    
class FixedDataFormat(AbstractDataFormat):
    """Data format for fixed data."""
    def __init__(self):
        self.lineDelimiter = None

    def getName(self):
        return FORMAT_FIXED

class OdsDataFormat(AbstractDataFormat):
    """Data format for ODS as created by OpenOffice.org's Calc."""
    # FIXME: Clean up inheritance hierarchy. We get a lot of junk from AbstractDataFormat.
    def getName(self):
        return FORMAT_ODS
