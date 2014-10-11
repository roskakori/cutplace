"""
Data formats that describe the general structure of the data.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import codecs
import logging
import io
import token
import tokenize

from cutplace import ranges
from cutplace import tools
from cutplace import _tools


ANY = "any"
CR = "cr"
LF = "lf"
CRLF = "crlf"


_LINE_DELIMITER_TO_TEXT_MAP = {
    ANY: ANY,
    "\n": LF,
    "\r": CR,
    "\r\n": CRLF
}


# Build reverse mapping for `_LINE_DELIMITER_TO_TEXT_MAP`.
_TEXT_TO_LINE_DELIMITER_MAP = {}
for lineDelimiter, lineDelimiterText in list(_LINE_DELIMITER_TO_TEXT_MAP.items()):
    _TEXT_TO_LINE_DELIMITER_MAP[lineDelimiterText] = lineDelimiter


_VALID_LINE_DELIMITER_TEXTS = sorted(_LINE_DELIMITER_TO_TEXT_MAP.values())
_VALID_LINE_DELIMITERS = sorted(_LINE_DELIMITER_TO_TEXT_MAP.keys())
_VALID_QUOTE_CHARACTERS = ["\"", "\'"]
_VALID_ESCAPE_CHARACTERS = ["\"", "\\"]
_VALID_DECIMAL_SEPARATORS = [".", ","]
_VALID_THOUSANDS_SEPARATORS = [",", ".", ""]
_VALID_FORMATS = ['delimited', 'excel', 'fixed', 'ods']


FORMAT_DELIMITED = "delimited"
FORMAT_EXCEL = "excel"
FORMAT_FIXED = "fixed"
FORMAT_ODS = "ods"


KEY_ALLOWED_CHARACTERS = "allowed_characters"
KEY_ENCODING = "encoding"
KEY_ESCAPE_CHARACTER = "escape_character"
KEY_FORMAT = "format"
KEY_HEADER = "header"
KEY_ITEM_DELIMITER = "item_delimiter"
KEY_LINE_DELIMITER = "line_delimiter"
KEY_QUOTE_CHARACTER = "quote_character"
KEY_SHEET = "sheet"
KEY_SPACE_AROUND_DELIMITER = "space_around_delimiter"
KEY_DECIMAL_SEPARATOR = "decimal_separator"
KEY_THOUSANDS_SEPARATOR = "thousands_separator"

class Dataformat():
    """
    Stores the data used by a dataformat.
    """

    def __init__(self, format_name):
        if format_name not in _VALID_FORMATS:
            raise ValueError('format is %s but must be on of: %s' % (format_name, _VALID_FORMATS))
        else:
            self._format = format_name
            self._header = 0
            self._allowed_characters = None
            self._encoding = 'cp1252'
            self._thousands_separator = ''
            if self.format == FORMAT_DELIMITED:
                self._item_delimiter = ','
                self._space_around_delimiter = False

            if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
                self._decimal_separator = ','
                self._escape_character = '"'
                self._line_delimiter = None
                self._quote_character = '"'
            elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
                self._sheet = 1

    @property
    def format(self):
        return self._format

    @property
    def encoding(self):
        return self._encoding

    @property
    def allowed_characters(self):
        return self._allowed_characters

    @property
    def escape_character(self):
        return self._escape_character

    @property
    def header(self):
        return self._header

    @property
    def item_delimiter(self):
        return self._item_delimiter

    @property
    def line_delimiter(self):
        return self._line_delimiter

    @property
    def quote_character(self):
        return self._quote_character

    @property
    def sheet(self):
        return self._sheet

    @property
    def space_around_delimiter(self):
        return self._space_around_delimiter

    @property
    def decimal_separator(self):
        return self._decimal_separator

    @property
    def thousands_separator(self):
        return self._thousands_separator

    def set_property(self, name, value):
        """
        Setting the value auf a property, used by a dataformat
        """
        varname = '_' + name
        if varname not in self.__dict__:
            raise ValueError('format %s does not support property %s' % (self.format, name))

        if name == KEY_ENCODING:
            try:
                codecs.lookup(value)
            except:
                #raise DataFormatValueError("value for data format property %r is %r but must be a valid encoding" % (key, value))
                raise ValueError("value for data format property %r is %r but must be a valid encoding" % (KEY_ENCODING, self.encoding))
            self._encoding = value
        elif name == KEY_HEADER:
            try:
                self._header = int(value)
            except ValueError:
                raise ValueError("header %s must be a number" % (value))
        elif name == KEY_ALLOWED_CHARACTERS:
            try:
                ranges.Range(value)
            except ranges.RangeSyntaxError as error:
                raise ValueError("value for property %r must be a valid range: %s" % (KEY_ALLOWED_CHARACTERS, error))
            self._allowed_characters = value
        elif name == KEY_LINE_DELIMITER:
            try:
                self._line_delimiter = _TEXT_TO_LINE_DELIMITER_MAP[value]
            except KeyError:
                raise ValueError("line delimiter %s must be changed to one of: %s"
                                 % (value, _VALID_LINE_DELIMITER_TEXTS))
        elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
            if name == KEY_SHEET:
                try:
                    self._sheet = int(value)
                except ValueError:
                    raise ValueError("sheet %s must be a number" % (value))
            else:
                raise ValueError("Property %s is not valid for excel format"%name)
        elif self.format == FORMAT_FIXED:
            self.__dict__[varname] = value
        elif self.format == FORMAT_DELIMITED:
            if name == KEY_SPACE_AROUND_DELIMITER:
                if value in ("True", "true"):
                    self._space_around_delimiter = True
                else:
                    self._space_around_delimiter = False
            else:
                self.__dict__[varname] = value

    def _validatedChoice(self, key, value, choices):
        """
        Validate that `value` is one of the available `choices` and otherwise raise `DataFormatValueError`.
        Always returns `value`. To be called from `validated()`.
        """
        assert key
        assert choices
        if value not in choices:
            #raise DataFormatValueError("value for data format property %r is %r but must be one of: %s"
            raise ValueError("value for data format property %r is %r but must be one of: %s" \
                  % (key, value, _tools.humanReadableList(choices)))
        return value


    def _validatedLong(self, key, value, lowerLimit=None):
        """
        Validate that ``value`` is a long number with a value of at least ``lowerLimit`` (if
        specified) and raise `DataFormatSyntaxError` if not.
        """
        assert key
        assert value is not None
        try:
            result = int(value)
        except ValueError:
            raise ValueError("value for data format property $r must be an integer number but is: $r" \
                  %(key, value))
            #raise DataFormatValueError("value for data format property %r must be an integer number but is: %r" % (key, value))
        if lowerLimit is not None:
            if result < lowerLimit:
                raise ValueError("value for data format property %r is %d but must be at least %d" \
                      %(key, result, lowerLimit))
                #raise DataFormatValueError("value for data format property %r is %d but must be at least %d" % (key, result, lowerLimit))
        return result


    def _validatedCharacter(self, key, value):
        r"""
        A single character intended as value for data format property ``key``
        derived from ``value``, which can be:

        * a decimal or hex number (prefixed with "0x") referring to the ASCII/Unicode of the character
        * a string containing a single character such as "\t".
        * a symbolic name such as "Tab".

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
        # TODO: Consolidate code with `ranges.__init__()`.
        assert key
        assert value is not None
        if len(value) == 1 and (value < "0" or value > "9"):
            result = value
        else:
            result = None
            tokens = tokenize.generate_tokens(io.StringIO(value).readline)
            nextToken = next(tokens)
            if _tools.isEofToken(nextToken):
                #raise DataFormatSyntaxError("value for data format property %r must be specified" % key)
                raise "value for data format property %r must be specified" %key
            nextType = nextToken[0]
            nextValue = nextToken[1]
            if nextType == token.NUMBER:
                try:
                    if nextValue[:2].lower() == "0x":
                        nextValue = nextValue[2:]
                        base = 16
                    else:
                        base = 10
                    longValue = int(nextValue, base)
                except ValueError:
                    raise ValueError("numeric value for data format property %r must be an integer but is: %r" %(key, value))
                    #raise DataFormatSyntaxError("numeric value for data format property %r must be an integer but is: %r" % (key, value))
            elif nextType == token.NAME:
                try:
                    longValue = tools.SYMBOLIC_NAMES_MAP[nextValue.lower()]
                except KeyError:
                    validSymbols = _tools.humanReadableList(sorted(tools.SYMBOLIC_NAMES_MAP.keys()))
                    #raise DataFormatSyntaxError("symbolic name %r for data format property %r must be one of: %s" % (value, key, validSymbols))
                    raise ValueError("symbolic name %r for data format property %r must be one of: %s" % (value, key, validSymbols))
            elif nextType == token.STRING:
                if len(nextValue) != 3:
                    #raise DataFormatSyntaxError("text for data format property %r must be a single character but is: %r" % (key, value))
                    raise ValueError("text for data format property %r must be a single character but is: %r" %(key, value))
                leftQuote = nextValue[0]
                rightQuote = nextValue[2]
                assert leftQuote in "\"\'", "leftQuote=%r" % leftQuote
                assert rightQuote in "\"\'", "rightQuote=%r" % rightQuote
                longValue = ord(nextValue[1])
            else:
                #raise DataFormatSyntaxError("value for data format property %r must a number, a single character or a symbolic name but is: %r" % (key, value))
                raise ValueError("value for data format property %r must a number, a single character or a symbolic name but is: %r" %(key, value))
            # Ensure there are no further tokens.
            nextToken = next(tokens)
            if not _tools.isEofToken(nextToken):
                #raise DataFormatSyntaxError("value for data format property %r must describe a single character but is: %r" % (key, value))
                raise ValueError("value for data format property %r must describe a single character but is: %r" %(key, value))
            assert longValue is not None
            assert longValue >= 0
            result = chr(longValue)
        assert result is not None
        return result


    def validate(self):
        """
        Validate all properties.
        """
        try:
            codecs.lookup(self.encoding)
        except:
            #raise DataFormatValueError("value for data format property %r is %r but must be a valid encoding" % (key, value))
            raise ValueError("value for data format property %r is %r but must be a valid encoding" % (KEY_ENCODING, self.encoding))

        try:
            ranges.Range(self.allowed_characters)
        except ranges.RangeSyntaxError as error:
            raise ValueError("value for property %r must be a valid range: %s" % (KEY_ALLOWED_CHARACTERS, error))

        self._validatedLong(KEY_HEADER, self.header, 0)

        if self.format in (FORMAT_EXCEL, FORMAT_ODS):
            self._validatedLong(KEY_SHEET, self.sheet, 1)

        if self.format == FORMAT_DELIMITED:
            self._validatedCharacter(KEY_ITEM_DELIMITER, self.item_delimiter)

            if self.space_around_delimiter in ("True", "true"):
                self._space_around_delimiter = True
            else:
                self._space_around_delimiter = False

        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            self._validatedChoice(KEY_DECIMAL_SEPARATOR, self.decimal_separator, _VALID_DECIMAL_SEPARATORS)

            self._validatedChoice(KEY_THOUSANDS_SEPARATOR, self.thousands_separator, _VALID_THOUSANDS_SEPARATORS)

            self._validatedChoice(KEY_ESCAPE_CHARACTER, self.escape_character, _VALID_ESCAPE_CHARACTERS)

            self._validatedChoice(KEY_QUOTE_CHARACTER, self.quote_character, _VALID_QUOTE_CHARACTERS)

            if(self._line_delimiter != None and self._line_delimiter not in _LINE_DELIMITER_TO_TEXT_MAP):
                try:
                    self._line_delimiter = _TEXT_TO_LINE_DELIMITER_MAP[self.line_delimiter]
                except KeyError:
                    raise ValueError("line delimiter %s must be changed to one of: %s"
                        % (self.line_delimiter, _VALID_LINE_DELIMITER_TEXTS))

            if self.decimal_separator == self.thousands_separator:
                raise ValueError("decimal separator can not equals thousands separator")
            if self.quote_character == self.thousands_separator:
                raise ValueError("quote character can not equals thousands separator")
            if self.thousands_separator == self.item_delimiter:
                raise ValueError("thousands separator can not equals item delimiter")
            if self.quote_character == self.item_delimiter:
                raise ValueError("quote character can not equals item delimiter")
            if self.line_delimiter == self.item_delimiter:
                raise ValueError("line delimiter can not equals item delimiter")
            if self.escape_character == self.item_delimiter:
                raise ValueError("escape character can not equals item delimiter")