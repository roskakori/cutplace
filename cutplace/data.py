"""
Data formats that describe the general structure of the data.
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
import codecs
import logging
import string
import StringIO
import token
import tokenize

import range
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
        DataFormatValueError: value for property 'allowed characters' must be a valid range: symbolic name 'spam' must be one of: 'cr', 'ff', 'lf', 'tab' or 'vt'
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
        self._log = logging.getLogger("cutplace")

        
    def _validatedCharacter(self, key, value):
        r"""
        A single character intended as value for data format property `key`
        derived from `value`, which can be:
        
        * a decimal or hex number (prefixed with "0x") referring to the ASCII/Unicode of the character
        * a string containing a single character such as "\t".
        * a symbolic name such as `Tab`.
        
        Anything else yields a `DataFormatSyntaxError`.
        
        >>> format = DelimitedDataFormat()
        >>> format._validatedCharacter("x", "34")
        '"'
        >>> format._validatedCharacter("x", "9")
        '\t'
        >>> format._validatedCharacter("x", "0x9")
        '\t'
        >>> format._validatedCharacter("x", "Tab")
        '\t'
        >>> format._validatedCharacter("x", "\t")
        '\t'
        >>> format._validatedCharacter("x", "")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: value for data format property 'x' must be specified
        >>> format._validatedCharacter("x", "Tab Tab")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: value for data format property 'x' must describe a single character but is: 'Tab Tab'
        >>> format._validatedCharacter("x", "17.23")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: numeric value for data format property 'x' must be an integer but is: '17.23'
        >>> format._validatedCharacter("x", "Hugo")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: symbolic name 'Hugo' for data format property 'x' must be one of: 'cr', 'ff', 'lf', 'tab' or 'vt'
        >>> format._validatedCharacter("x", "( ")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: value for data format property 'x' must a number, a single character or a symbolic name but is: '( '
        >>> format._validatedCharacter("x", "\"\\")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: value for data format property 'x' must a number, a single character or a symbolic name but is: '"\\'
        >>> format._validatedCharacter("x", "\"abc\"")
        Traceback (most recent call last):
            ...
        DataFormatSyntaxError: text for data format property 'x' must be a single character but is: '"abc"'
        """
        # TODO: Consolidate code with `Range.__init__()`.
        assert key
        assert value is not None
        if len(value) == 1 and (value < "0" or value > "9"):
            # TODO: Remove support for deprecated syntax.
            result = value
            self._log.warning("value %r for data format property %r should be put between double quotes: \"%s\"" % (value, key, value))
        else:
            result = None
            tokens = tokenize.generate_tokens(StringIO.StringIO(value).readline)
            next = tokens.next()
            if tools.isEofToken(next):
                raise DataFormatSyntaxError("value for data format property %r must be specified" % key)
            nextType = next[0]
            nextValue = next[1]
            if nextType == token.NUMBER:
                try:
                    if nextValue[:2].lower() == "0x":
                        nextValue = nextValue[2:]
                        base = 16
                    else:
                        base = 10
                    longValue = long(nextValue, base)
                except ValueError, error:
                    raise DataFormatSyntaxError("numeric value for data format property %r must be an integer but is: %r" % (key, value))
            elif nextType == token.NAME:
                try:
                    longValue = tools.SYMBOLIC_NAMES_MAP[nextValue.lower()]
                except KeyError:
                    validSymbols = tools.humanReadableList(sorted(tools.SYMBOLIC_NAMES_MAP.keys()))
                    raise DataFormatSyntaxError("symbolic name %r for data format property %r must be one of: %s" % (value, key, validSymbols))
            elif nextType == token.STRING:
                if len(nextValue) != 3:
                    raise DataFormatSyntaxError("text for data format property %r must be a single character but is: %r" % (key, value))
                leftQuote = nextValue[0]
                rightQuote = nextValue[2]
                assert leftQuote in "\"\'", "leftQuote=%r" % leftQuote 
                assert rightQuote in "\"\'", "rightQuote=%r" % rightQuote
                longValue = ord(nextValue[1])
            else:
                raise DataFormatSyntaxError("value for data format property %r must a number, a single character or a symbolic name but is: %r" % (key, value))
            # Ensure there are no further tokens.
            next = tokens.next()
            if not tools.isEofToken(next):
                raise DataFormatSyntaxError("value for data format property %r must describe a single character but is: %r" % (key, value))

            assert longValue is not None
            assert longValue >= 0
            result = chr(longValue)
        assert result is not None
        return result

    def validated(self, key, value):
        assert key == self._normalizedKey(key)
        
        if key == KEY_ESCAPE_CHARACTER:
            result = self._validatedChoice(key, value, _VALID_ESCAPE_CHARACTERS)
        elif key == KEY_ITEM_DELIMITER:
            result = self._validatedCharacter(key, value)
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
        
    def strippedOfBlanks(self, value):
        """
        `value` but with leading and trailing blanks removed.
        
        >>> format = FixedDataFormat()
        >>> format.strippedOfBlanks(" before")
        'before'
        >>> format.strippedOfBlanks("after  ")
        'after'
        >>> format.strippedOfBlanks("   both \t ")
        'both'
        >>> format.strippedOfBlanks("")
        ''

        Note: For this test, there is not way to make doctest preserve the
        "\t" in the output, though the result still contains it.
        >>> format.strippedOfBlanks("nothing to\t strip")
        'nothing to  strip'
        """
        assert value is not None
        # FIXME: Take data format property "blanks" (or whatever it is named) into account.
        result = value.strip()
        return result

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
