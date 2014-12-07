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
import io
import token
import tokenize

from cutplace import errors
from cutplace import ranges
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
for line_delimiter, line_delimiter_text in list(_LINE_DELIMITER_TO_TEXT_MAP.items()):
    _TEXT_TO_LINE_DELIMITER_MAP[line_delimiter_text] = line_delimiter


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
KEY_SKIP_INITIAL_SPACE = "skip_initial_space"
KEY_DECIMAL_SEPARATOR = "decimal_separator"
KEY_THOUSANDS_SEPARATOR = "thousands_separator"


class DataFormat():
    """
    General data format of a file describing the basic structure.
    """

    def __init__(self, format_name, location=None):
        if format_name not in _VALID_FORMATS:
            raise errors.InterfaceError('format is %s but must be on of: %s'
                                        % (format_name, _VALID_FORMATS), location)
        else:
            self._location = location
            self._format = format_name
            self._header = 0
            self._allowed_characters = None
            self._encoding = 'cp1252'
            self._thousands_separator = ''
            if self.format == FORMAT_DELIMITED:
                self._item_delimiter = ','
                self._skip_initial_space = False
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
    def skip_initial_space(self):
        return self._skip_initial_space

    @property
    def decimal_separator(self):
        return self._decimal_separator

    @property
    def thousands_separator(self):
        return self._thousands_separator

    def set_property(self, name, value):
        """
        Set the value of a data format property. In case the property or
        value cannot be processed, raise `errors.InterfaceError`.
        """
        name = name.replace(' ', '_')
        varname = '_' + name
        if varname not in self.__dict__:
            raise errors.InterfaceError(
                'format %s does not support property %s' % (self.format, name), self._location)

        if name == KEY_ENCODING:
            try:
                codecs.lookup(value)
            except:
                raise errors.InterfaceError('value for data format property %r is %r but must be a valid encoding'
                                            % (KEY_ENCODING, self.encoding), self._location)
            self._encoding = value
        elif name == KEY_HEADER:
            try:
                self._header = int(value)
            except ValueError:
                raise errors.InterfaceError('header %s must be a number' % value, self._location)
        elif name == KEY_ALLOWED_CHARACTERS:
            try:
                self._allowed_characters = ranges.Range(value)
            except errors.InterfaceError as error:
                raise errors.InterfaceError('value for property %r must be a valid range: %s'
                                            % (KEY_ALLOWED_CHARACTERS, error), self._location)
        elif name == KEY_LINE_DELIMITER:
            try:
                self._line_delimiter = _TEXT_TO_LINE_DELIMITER_MAP[value]
            except KeyError:
                raise errors.InterfaceError('line delimiter %s must be changed to one of: %s'
                                            % (value, _VALID_LINE_DELIMITER_TEXTS), self._location)
        elif name == KEY_ITEM_DELIMITER:
            self._item_delimiter = self._validated_character(KEY_ITEM_DELIMITER, value)
        elif name == KEY_DECIMAL_SEPARATOR:
            self._decimal_separator = self._validated_choice(KEY_DECIMAL_SEPARATOR, value, _VALID_DECIMAL_SEPARATORS)
        elif name == KEY_THOUSANDS_SEPARATOR:
            self._thousands_separator = self._validated_choice(
                KEY_DECIMAL_SEPARATOR, value, _VALID_THOUSANDS_SEPARATORS)
        elif name == KEY_ESCAPE_CHARACTER:
            self._escape_character = self._validated_choice(KEY_ESCAPE_CHARACTER, value, _VALID_ESCAPE_CHARACTERS)
        elif name == KEY_QUOTE_CHARACTER:
            self._quote_character = self._validated_choice(KEY_QUOTE_CHARACTER, value, _VALID_QUOTE_CHARACTERS)
        elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
            if name == KEY_SHEET:
                try:
                    self._sheet = int(value)
                except ValueError:
                    raise errors.InterfaceError('sheet %s must be a number' % value, self._location)
            else:
                raise errors.InterfaceError('property %s is not valid for excel format' % name, self._location)
        elif self.format == FORMAT_FIXED:
            self.__dict__[varname] = value
        elif self.format == FORMAT_DELIMITED:
            if name == KEY_SKIP_INITIAL_SPACE:
                if value in ('True', 'true'):
                    self._skip_initial_space = True
                elif value in ('False', 'false'):
                    self._skip_initial_space = False
                else:
                    raise errors.InterfaceError('skip initial space %s must be changed to one of: True, False'
                                                % value, self._location)
            else:
                self.__dict__[varname] = value

    def _validated_choice(self, key, value, choices):
        """
        Validate that `value` is one of the available `choices` and otherwise raise `errors.InterfaceError`.
        Always returns `value`. To be called from `validated()`.
        """
        assert key
        assert choices
        if value not in choices:
            raise errors.InterfaceError('value for data format property %r is %r but must be one of: %s'
                                        % (key, value, _tools.humanReadableList(choices)), self._location)
        return value

    def _validated_character(self, key, value):
        r"""
        A single character intended as value for data format property ``key``
        derived from ``value``, which can be:

        * a decimal or hex number (prefixed with "0x") referring to the ASCII/Unicode of the character
        * a string containing a single character such as "\t".
        * a symbolic name such as "Tab".

        Anything else yields a `InterfaceError`.
        >>> format = DelimitedDataFormat()
        >>> format._validated_character("x", "34")
        '"'
        >>> format._validated_character("x", "9")
        '\t'
        >>> format._validated_character("x", "0x9")
        '\t'
        >>> format._validated_character("x", "Tab")
        '\t'
        >>> format._validated_character("x", "\t")
        '\t'
        >>> format._validated_character("x", "")
        Traceback (most recent call last):
            ...
        InterfaceError: value for data format property 'x' must be specified
        >>> format._validated_character("x", "Tab Tab")
        Traceback (most recent call last):
            ...
        InterfaceError: value for data format property 'x' must describe a single character but is: 'Tab Tab'
        >>> format._validated_character("x", "17.23")
        Traceback (most recent call last):
            ...
        InterfaceError: numeric value for data format property 'x' must be an integer but is: '17.23'
        >>> format._validated_character("x", "Hugo")
        Traceback (most recent call last):
            ...
        InterfaceError: symbolic name 'Hugo' for data format property 'x' must be one of:
        'cr', 'ff', 'lf', 'tab' or 'vt'
        >>> format._validated_character("x", "( ")
        Traceback (most recent call last):
            ...
        InterfaceError: value for data format property 'x' must a number, a single character or
        a symbolic name but is: '( '
        >>> format._validated_character("x", "\"\\")
        Traceback (most recent call last):
            ...
        InterfaceError: value for data format property 'x' must a number, a single character or
        a symbolic name but is: '"\\'
        >>> format._validated_character("x", "\"abc\"")
        Traceback (most recent call last):
            ...
        InterfaceError: text for data format property 'x' must be a single character but is: '"abc"'
        """
        # TODO: Consolidate code with `ranges.__init__()`.
        assert key
        assert value is not None
        if len(value) == 1 and (value < "0" or value > "9"):
            result = value
        else:
            result = None
            tokens = tokenize.generate_tokens(io.StringIO(value).readline)
            next_token = next(tokens)
            if _tools.isEofToken(next_token):
                raise errors.InterfaceError("value for data format property %r must be specified" % key,
                                            self._location)
            next_type = next_token[0]
            next_value = next_token[1]
            if next_type == token.NUMBER:
                try:
                    if next_value[:2].lower() == "0x":
                        next_value = next_value[2:]
                        base = 16
                    else:
                        base = 10
                    long_value = int(next_value, base)
                except ValueError:
                    raise errors.InterfaceError(
                        'numeric value for data format property %r must be an integer but is: %r'
                        % (key, value), self._location)
            elif next_type == token.NAME:
                try:
                    long_value = errors.NAME_TO_ASCII_CODE_MAP[next_value.lower()]
                except KeyError:
                    valid_symbols = _tools.humanReadableList(sorted(errors.NAME_TO_ASCII_CODE_MAP.keys()))
                    raise errors.InterfaceError('symbolic name %r for data format property %r must be one of: %s'
                                                % (value, key, valid_symbols), self._location)
            elif next_type == token.STRING:
                if len(next_value) != 3:
                    raise errors.InterfaceError(
                        'text for data format property %r must be a single character but is: %r'
                        % (key, value), self._location)
                left_quote = next_value[0]
                right_quote = next_value[2]
                assert left_quote in "\"\'", "leftQuote=%r" % left_quote
                assert right_quote in "\"\'", "rightQuote=%r" % right_quote
                long_value = ord(next_value[1])
            else:
                raise errors.InterfaceError(
                    'value for data format property %r must a number, a single character or a symbolic name but is: %r'
                    % (key, value), self._location)
            # Ensure there are no further tokens.
            next_token = next(tokens)
            if not _tools.isEofToken(next_token):
                raise errors.InterfaceError(
                    'value for data format property %r must describe a single character but is: %r'
                    % (key, value), self._location)
            assert long_value is not None
            assert long_value >= 0
            result = chr(long_value)
        assert result is not None
        return result

    def validate(self):
        """
        Validate necessary properties.
        """
        if self.decimal_separator == self.thousands_separator:
            raise errors.InterfaceError('decimal separator and thousands separator must be different', self._location)
        if self.quote_character == self.thousands_separator:
            raise errors.InterfaceError('quote character and thousands separator must be different', self._location)
        if self.thousands_separator == self.item_delimiter:
            raise errors.InterfaceError('thousands separator and item delimiter must be different', self._location)
        if self.quote_character == self.item_delimiter:
            raise errors.InterfaceError('quote character and item delimiter must be different', self._location)
        if self.line_delimiter == self.item_delimiter:
            raise errors.InterfaceError('line delimiter and item delimiter must be different', self._location)
        if self.escape_character == self.item_delimiter:
            raise errors.InterfaceError('escape character and item delimiter must be different', self._location)
        self._location = None
