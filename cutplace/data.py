"""
Data formats that describe the general structure of the data.
"""
import codecs
import logging
import range
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
FORMAT_EXCEL = "excel"
FORMAT_FIXED = "fixed"
FORMAT_ODS = "ods"

KEY_ALLOWED_CHARACTERS = "allowed characters"
KEY_ENCODING = "encoding"
KEY_ESCAPE_CHARACTER = "escape character"
KEY_FORMAT = "format"
KEY_HEADER = "header"
KEY_ITEM_DELIMITER = "item delimiter"
KEY_LINE_DELIMITER = "line delimiter"
KEY_QUOTE_CHARACTER = "quote character"
KEY_SHEET = "sheet"
KEY_SPACE_AROUND_DELIMITER = "blanks around delimiter"

# TODO: Add KEY_DECIMAL_SEPARATOR = "decimalSeparator"
# TODO: Add KEY_THOUSANDS_SEPARATOR = "thousandsSeparator"

def createDataFormat(name):
    """
    Factory function to create the specified data format.
    """
    assert name is not None

    _NAME_TO_FORMAT_MAP = {
                            FORMAT_CSV: CsvDataFormat,
                            FORMAT_DELIMITED: DelimitedDataFormat,
                            FORMAT_EXCEL: ExcelDataFormat,
                            FORMAT_FIXED: FixedDataFormat,
                            FORMAT_ODS: OdsDataFormat
                           }
    actualName = name.lower()
    formatClass = _NAME_TO_FORMAT_MAP.get(actualName)
    if formatClass is None:
        dataFormatNames = _NAME_TO_FORMAT_MAP.keys()
        dataFormatNames.sort()
        raise DataFormatSyntaxError("data format is %r but must be one of: %r"
                                    % (actualName, tools.humanReadableList(dataFormatNames)))
    result = formatClass()
    return result

def _isKey(possibleKey, keyToCompareWith):
    """
    True if `possibleKey` and `keyToCompareWith` match, ignoring case and blanks between words.
    """ 
    possibleKeyWords = possibleKey.lower().split()
    keyToCompareWithWords = keyToCompareWith.lower().split()
    return possibleKeyWords == keyToCompareWithWords

def isFormatKey(key):
    """
    True if `key` matches `KEY_FORMAT`.
    """
    return _isKey(key, KEY_FORMAT)

class DataFormatValueError(tools.CutplaceError):
    """
    Error in data caused by violating the data format.
    """

class DataFormatSyntaxError(tools.CutplaceError):
    """
    Error in data format declaration.
    """

class _BaseDataFormat(object):
    """
    Data format acting as base for other data formats.
    
    The only function you really need to overwrite is `validated()`.
    """
    def __init__(self, requiredKeys, optionalKeyValueMap):
        """
        Setup new format with `requiredKeys`being a list of property names that must be set, and
        `optionalKeyValueMap` being a dictionary where they keys denote property names and the
        values describe default values that should be used in case the property is never set.
        """
        self.requiredKeys = []
        self.optionalKeyValueMap = {KEY_ALLOWED_CHARACTERS:None, KEY_HEADER: 0}
        if requiredKeys is not None:
            self.requiredKeys.extend(requiredKeys)
        if optionalKeyValueMap is not None:
            self.optionalKeyValueMap.update(optionalKeyValueMap)
        self.properties = {}
        self._allKeys = []
        self._allKeys.extend(self.requiredKeys)
        self._allKeys.extend(self.optionalKeyValueMap.keys())
        for key in self._allKeys:
            assert key == self._normalizedKey(key), "key must be normalized: %r" % (key)
    
    def _normalizedKey(self, key):
        assert key is not None
        
        # Normalize key.
        keyParts = key.lower().split()
        result = ""
        for keyPart in keyParts:
            if result:
                result += " "
            result += keyPart
            
        # Validate key.
        if result not in self._allKeys:
            raise DataFormatSyntaxError("data format property is %r but must be one of: %s"
                                        % (result, tools.humanReadableList(self._allKeys)))

        return result

    def _validatedChoice(self, key, value, choices):
        """
        Validate that `value` is one of the available `choices` and otherwise raise `DataFormatValueError`.
        Always returns `value`. To be called from `validated()`.
        """
        assert key
        assert choices
        if value not in choices:
            raise DataFormatValueError("value for data format property %r is %r but must be one of: %s" 
                                       % (key, value, tools.humanReadableList(choices)))
        return value
    
    def _validatedLong(self, key, value, lowerLimit=None):
        """
        Validate that `value`is a long number with a value of at least `lowerLimit` (if specified)
        and raise `DataFormatSyntaxError` if not.
        """
        assert key
        assert value is not None
        
        try:
            result = long(value)
        except ValueError, error:
            raise DataFormatValueError("value for data format property %r is %r but must be an integer number" % (key, value))
        if lowerLimit is not None:
            if result < lowerLimit:
                raise DataFormatValueError("value for data format property %r is %d but must be at least %d" % (key, result, lowerLimit))
        return result
            
    def validated(self, key, value):
        """
       `Value` in its native type.
       
       If `key` can not be handled, raise `DataFormaSyntaxError`.

       If `value` can not be handled, raise `DataFormaValueError`.

        This function should be overwritten by child classes, but also be called by them via
        `super` in case the child cannot handle `key` in order to consistently handle the
        standard keys.
        """
        if key == KEY_ALLOWED_CHARACTERS:
            try:
                result = range.Range(value)
            except range.RangeSyntaxError, error:
                raise DataFormatValueError("value for property %r must be a valid range: %s" % (key, error))
        elif key == KEY_HEADER:
            result = self._validatedLong(key, value, 0)
        else:  # pragma: no cover
            assert False, "_normalizedKey() must detect broken property name %r" % key
        return result

    def validateAllRequiredPropertiesHaveBeenSet(self):
        """
        Validate that all required properties have been set and if not, raise
        `DataFormatSyntaxError`.
        """
        for requiredKey in self.requiredKeys:
            if requiredKey not in self.properties:
                raise DataFormatSyntaxError("required data format property must be set: %r" % requiredKey)
            
    def set(self, key, value):
        r"""
        Attempt to set `key`to `value`.

        >>> format = createDataFormat(FORMAT_CSV)
        >>> format.set(KEY_LINE_DELIMITER, LF)
        
        In case the key has already been set, raise a `DataValueError`.

        >>> format.set(KEY_LINE_DELIMITER, CR)
        Traceback (most recent call last):
            ...
        DataFormatValueError: data format property 'line delimiter' has already been set: '\n'
        
        In case `value` can not be used for `key`, reraise the error raised by `validated()`.

        >>> format.set(KEY_ALLOWED_CHARACTERS, "spam")
        Traceback (most recent call last):
            ...
        DataFormatValueError: value for property 'allowed characters' must be a valid range: range must be specified using integer numbers and colon (:) but found: 'spam' [token type: 1]
        """
        normalizedKey = self._normalizedKey(key)
        if normalizedKey in self.properties:
            raise DataFormatValueError("data format property %r has already been set: %r" % (key, self.properties[normalizedKey]))
        self.properties[normalizedKey] = self.validated(normalizedKey, value)
    
    def get(self, key):
        r"""
        The value of `key`, or its default value (as specified with `__init__()`) in case it has
        not be set yet, or `None` if no default value exists.
        
        Note that the result does not have to be the same value that has been passed to `set()`
        because for some keys the value for `set()` is in a human readable representation whereas
        the result of `get()` can be an internal representation.
        
        >>> format = createDataFormat(FORMAT_CSV)
        >>> format.set(KEY_LINE_DELIMITER, LF)
        >>> print "%r" % format.get(KEY_LINE_DELIMITER)
        '\n'
        """
        normalizedKey = self._normalizedKey(key)
        defaultValue = self.optionalKeyValueMap.get(normalizedKey)
        return self.properties.get(normalizedKey, defaultValue)

    def _getEncoding(self):
        return self.get(KEY_ENCODING)
        
    def _setEncoding(self, value):
         self.set(KEY_ENCODING, value)
         
    encoding = property(_getEncoding, _setEncoding)

    def __str__(self):
        return "DataFormat(%r, %r)" % (self.name, self.properties)
    
class _BaseTextDataFormat(_BaseDataFormat):
    """
    Base data format that supports an "encoding" and "line delimiter" property.
    """
    def __init__(self, name, optionalKeyValueMap):
        assert name
        actualOptionalKeyValueMap = {KEY_LINE_DELIMITER: None}
        if optionalKeyValueMap is not None:
            actualOptionalKeyValueMap.update(optionalKeyValueMap)
        super(_BaseTextDataFormat, self).__init__([KEY_ENCODING], actualOptionalKeyValueMap)
        self.name = name

    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ENCODING:
            try:
                # Validate encoding name.
                codecs.lookup(value)
            except:
                raise DataFormatValueError("value for data format property %r is %r but must be a valid encoding" % (key, value))
            result = value
        elif key == KEY_LINE_DELIMITER:
            lowerValue = value.lower()
            self._validatedChoice(key, lowerValue, _VALID_LINE_DELIMITER_TEXTS)
            lineDelimiterIndex = _VALID_LINE_DELIMITER_TEXTS.index(lowerValue)
            result = _VALID_LINE_DELIMITERS[lineDelimiterIndex]
        else:
            result = super(_BaseTextDataFormat, self).validated(key, value)
        return result

class _BaseSpreadsheetDataFormat(_BaseDataFormat):
    """
    Base data format for spreadsheet formats.
    """
    def __init__(self, name):
        assert name
        
        super(_BaseSpreadsheetDataFormat, self).__init__(None, {KEY_SHEET: 1})
        self.name = name
        
    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_SHEET:
            result = self._validatedLong(key, value, 1)
        else:
            result = super(_BaseSpreadsheetDataFormat, self).validated(key, value)

        return result

class DelimitedDataFormat(_BaseTextDataFormat):
    """
    Data format for delimited data such as CSV.
    """
    def __init__(self, lineDelimiter=ANY, itemDelimiter=ANY):
        assert lineDelimiter is not None
        assert lineDelimiter in  _VALID_LINE_DELIMITERS
        assert (itemDelimiter == ANY) or (len(itemDelimiter) == 1)
        
        super(DelimitedDataFormat, self).__init__(
                                              FORMAT_DELIMITED,
                                              {KEY_ESCAPE_CHARACTER: None,
                                               KEY_ITEM_DELIMITER: itemDelimiter,
                                               KEY_QUOTE_CHARACTER:None})
        self.optionalKeyValueMap[KEY_LINE_DELIMITER] = lineDelimiter
        
    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ESCAPE_CHARACTER:
            result = self._validatedChoice(key, value, _VALID_ESCAPE_CHARACTERS)
        elif key == KEY_ITEM_DELIMITER:
            result = value
        elif key == KEY_QUOTE_CHARACTER:
            result = self._validatedChoice(key, value, _VALID_QUOTE_CHARACTERS)
        else:
            result = super(DelimitedDataFormat, self).validated(key, value)

        return result

class CsvDataFormat(DelimitedDataFormat):
    """
    Data format for comma separated values (CSV).
    """
    def __init__(self):
        super(CsvDataFormat, self).__init__()
        assert self.get(KEY_LINE_DELIMITER) == ANY
        assert self.get(KEY_ITEM_DELIMITER) == ANY

        self.name = FORMAT_CSV
        self.optionalKeyValueMap[KEY_ENCODING] = u"ascii"
        self.optionalKeyValueMap[KEY_QUOTE_CHARACTER] = u"\""
        self.optionalKeyValueMap[KEY_ESCAPE_CHARACTER] = u"\""

class FixedDataFormat(_BaseTextDataFormat):
    """
    Data format for fixed data.
    """
    def __init__(self):
        super(FixedDataFormat, self).__init__(FORMAT_FIXED, None)

class OdsDataFormat(_BaseSpreadsheetDataFormat):
    """
    Data format for ODS as created by OpenOffice.org's Calc.
    """
    def __init__(self):
        super(OdsDataFormat, self).__init__(FORMAT_ODS)

class ExcelDataFormat(_BaseSpreadsheetDataFormat):
    """
    Data format for Excel spreadsheets.
    """
    def __init__(self):
        super(ExcelDataFormat, self).__init__(FORMAT_EXCEL)
