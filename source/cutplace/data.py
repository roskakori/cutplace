"""
Data formats that describe the general structure of an input.
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
KEY_ITEM_DELIMITER = "item delimiter"
KEY_LINE_DELIMITER = "line delimiter"
KEY_QUOTE_CHARACTER = "quote character"
KEY_SPACE_AROUND_DELIMITER = "blanks around delimiter"

# TODO: Move validation of KEY_ALLOWED_CHARACTERS to _AbstractDataFormat because all formats support it.

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
        raise DataFormatSyntaxError("data format is %r but must be on of: %r"
                                    % (name, [FORMAT_CSV, FORMAT_DELIMITED, FORMAT_EXCEL, FORMAT_FIXED]))

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
    True if key matches KEY_FORMAT.
    """
    return _isKey(key, KEY_FORMAT)

class DataFormatValueError(tools.CutplaceError):
    pass

class DataFormatLookupError(tools.CutplaceError):
    pass

class DataFormatSyntaxError(tools.CutplaceError):
    pass

class _AbstractDataFormat(object):
    """
    Abstract data format acting as base for other data formats.
    
    The only function you really need to overwrite is `validated()`.
    """
    def __init__(self, requiredKeys, optionalKeyValueMap):
        """
        Setup new format with `requiredKeys`being a list of property names that must be set, and
        `optionalKeyValueMap` being a dictionary where they keys denote property names and the
        values describe default values that should be used in case the property is never set.
        """
        if requiredKeys is None:
            self.requiredKeys = []
        else:
            self.requiredKeys = requiredKeys
        if optionalKeyValueMap is None:
            self.optionalKeyValueMap = {}
        else:
            self.optionalKeyValueMap = optionalKeyValueMap
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
            raise DataFormatSyntaxError("key is %r but must be one of: %r" % (result, self._allKeys))

        return result

    def _validatedChoice(self, key, value, choices):
        """
        Validate that `value` is one of the available `choices` and otherwise raise `DataFormatValueError`.
        Always returns `value`. To be called from `validated()`.
        """
        assert key
        assert choices
        if value not in choices:
            raise DataFormatValueError("value for data format property %r is %r but must be one of: %r" % (key, value, choices))
        return value
            
    def validated(self, key, value):
        """
       `Value` in its native type.
       
       If `key` can not be handled, raise `DataFormatLookupError`.
       
       If `value`does not match expectations, raise `DataFormatValueError`.
       
       This function needs to be overwritten by ancestors, by default it just raises
       `NotImplementedError`.
        """
        raise NotImplementedError

    def validateAllRequiredPropertiesHaveBeenSet(self):
        """
        Validate that all required properties have been set and if not, raise
        `DataFormatSyntaxError`.
        """
        for requiredKey in self.requiredKeys:
            if requiredKey not in self.properties:
                raise DataFormatSyntaxError("required data format property must be set: %r" % requiredKey)
            
    def set(self, key, value):
        normalizedKey = self._normalizedKey(key)
        if normalizedKey in self.properties:
            raise DataFormatValueError("data format property %r has already been set: %r" % (key, self.properties[normalizedKey]))
        self.properties[normalizedKey] = self.validated(normalizedKey, value)
    
    def get(self, key):
        """
        The value of `key`, or its default value (as specified with `__init__()`) in case it has
        not be set yet, or `None` if no default value exists.
        """
        normalizedKey = self._normalizedKey(key)
        defaultValue = self.optionalKeyValueMap.get(normalizedKey)
        return self.properties.get(normalizedKey, defaultValue)

    
class DelimitedDataFormat(_AbstractDataFormat):
    """
    Data format for delimited data such as CSV.
    """
    def __init__(self, lineDelimiter=ANY, itemDelimiter=ANY):
        assert lineDelimiter is not None
        assert lineDelimiter in  _VALID_LINE_DELIMITERS
        assert (itemDelimiter == ANY) or (len(itemDelimiter) == 1)
        
        super(DelimitedDataFormat, self).__init__(
                                              [KEY_ENCODING],
                                              {KEY_ALLOWED_CHARACTERS: None,
                                               KEY_ESCAPE_CHARACTER: None,
                                               KEY_ITEM_DELIMITER: itemDelimiter,
                                               KEY_LINE_DELIMITER: lineDelimiter,
                                               KEY_QUOTE_CHARACTER:None})
        self.name = FORMAT_DELIMITED
        
    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ALLOWED_CHARACTERS:
            try:
                result = range.Range(value)
            except range.RangeSyntaxError, error:
                raise DataFormatSyntaxError("value for property %r must be a valid range: %s" % (key, str(error)))
        elif key == KEY_ENCODING:
            try:
                result = codecs.lookup(value)
            except:
                raise DataFormatSyntaxError("value for property %r is %r but must be a valid encoding" % (key, value))
        elif key == KEY_ESCAPE_CHARACTER:
            result = self._validatedChoice(key, value, _VALID_ESCAPE_CHARACTERS)
        elif key == KEY_ITEM_DELIMITER:
            result = value
        elif key == KEY_LINE_DELIMITER:
            lowerValue = value.lower()
            self._validatedChoice(key, lowerValue, _VALID_LINE_DELIMITER_TEXTS)
            lineDelimiterIndex = _VALID_LINE_DELIMITER_TEXTS.index(lowerValue)
            result = _VALID_LINE_DELIMITERS[lineDelimiterIndex]
        elif key == KEY_QUOTE_CHARACTER:
            result = self._validatedChoice(key, value, _VALID_QUOTE_CHARACTERS)
        else:
            raise NotImplementedError("key=%r" % key)
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
        self.optionalKeyValueMap[KEY_ENCODING] = codecs.lookup("ascii")
        self.optionalKeyValueMap[KEY_QUOTE_CHARACTER] = "\""
        self.optionalKeyValueMap[KEY_ESCAPE_CHARACTER] = "\""

class FixedDataFormat(_AbstractDataFormat):
    """
    Data format for fixed data.
    """
    def __init__(self):
        super(FixedDataFormat, self).__init__(
                                              [KEY_ENCODING],
                                              {KEY_ALLOWED_CHARACTERS: None,
                                               KEY_LINE_DELIMITER: None})
        self.name = FORMAT_FIXED

    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ALLOWED_CHARACTERS:
            try:
                result = range.Range(value)
            except range.RangeSyntaxError, error:
                raise DataFormatSyntaxError("value for property %r must be a valid range: %s" % (key, str(error)))
        elif key == KEY_ENCODING:
            try:
                result = codecs.lookup(value)
            except:
                raise DataFormatSyntaxError("value for property %r is %r but must be a valid encoding" % (key, value))
        elif key == KEY_LINE_DELIMITER:
            lowerValue = value.lower()
            self._validatedChoice(key, lowerValue, _VALID_LINE_DELIMITER_TEXTS)
            lineDelimiterIndex = _VALID_LINE_DELIMITER_TEXTS.index(lowerValue)
            result = _VALID_LINE_DELIMITERS[lineDelimiterIndex]
        else:
            raise NotImplementedError("key=%r" % key)
        return result

class OdsDataFormat(_AbstractDataFormat):
    """
    Data format for ODS as created by OpenOffice.org's Calc.
    """
    def __init__(self):
        super(OdsDataFormat, self).__init__(
                                              None,
                                              {KEY_ALLOWED_CHARACTERS: None})
        self.name = FORMAT_ODS

    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ALLOWED_CHARACTERS:
            try:
                result = range.Range(value)
            except range.RangeSyntaxError, error:
                raise DataFormatSyntaxError("value for property %r must be a valid range: %s" % (key, str(error)))
        else:
            raise NotImplementedError("key=%r" % key)
        return result

class ExcelDataFormat(_AbstractDataFormat):
    """
    Data format for Excel spreadsheets.
    """
    def __init__(self):
        super(ExcelDataFormat, self).__init__(
                                              None,
                                              {KEY_ALLOWED_CHARACTERS: None})
        self.name = FORMAT_EXCEL

    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ALLOWED_CHARACTERS:
            try:
                result = range.Range(value)
            except range.RangeSyntaxError, error:
                raise DataFormatSyntaxError("value for property %r must be a valid range: %s" % (key, str(error)))
        else:
            raise NotImplementedError("key=%r" % key)
        return result
