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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import io
import token
import tokenize

from cutplace import errors
from cutplace import ranges
from cutplace import _compat
from cutplace import _tools
from cutplace._compat import python_2_unicode_compatible

#: Value for property ``line_delimiter`` to indicate any possible delimiter.
ANY = "any"
#: Value for property ``line_delimiter`` to indicate carriage return (Mac OS Classic).
CR = "cr"
#: Value for property ``line_delimiter`` to line feed (Unix).
LF = "lf"
#: Value for property ``line_delimiter`` to indicate carriage return + line feed (Windows).
CRLF = "crlf"

#: A mapping for internal line delimiters (e.g. '\n') to the textual
#: representation in the CID (e.g. 'lf').
#:
#: Note: it would have been convenient to have keys with the same values as
#: `io.open()`'s ``newline`` parameter. However, ``newline`` does not
#: provide a value for "no newline" and already uses ``None`` to represent
#: 'any'.
LINE_DELIMITER_TO_TEXT_MAP = {
    ANY: ANY,
    "\n": LF,
    "\r": CR,
    "\r\n": CRLF,
    None: 'none',
}
_TEXT_TO_LINE_DELIMITER_MAP = dict([(value, key) for key, value in LINE_DELIMITER_TO_TEXT_MAP.items()])
assert len(LINE_DELIMITER_TO_TEXT_MAP) == len(_TEXT_TO_LINE_DELIMITER_MAP), \
    'values in LINE_DELIMITER_TO_TEXT_MAP must be unique'

#: Format name for delimited data.
FORMAT_DELIMITED = "delimited"
#: Format name for Excel data.
FORMAT_EXCEL = "excel"
#: Format name for fixed formatted data (PRN).
FORMAT_FIXED = "fixed"
#: Format name for Open Document spreadsheets (ODS).
FORMAT_ODS = "ods"

KEY_ALLOWED_CHARACTERS = "allowed_characters"
KEY_ENCODING = "encoding"
KEY_ESCAPE_CHARACTER = "escape_character"
KEY_HEADER = "header"
KEY_ITEM_DELIMITER = "item_delimiter"
KEY_LINE_DELIMITER = "line_delimiter"
KEY_QUOTE_CHARACTER = "quote_character"
KEY_SHEET = "sheet"
KEY_SKIP_INITIAL_SPACE = "skip_initial_space"
KEY_DECIMAL_SEPARATOR = "decimal_separator"
KEY_THOUSANDS_SEPARATOR = "thousands_separator"

_VALID_QUOTE_CHARACTERS = ["\"", "\'"]
_VALID_ESCAPE_CHARACTERS = ["\"", "\\"]
_VALID_DECIMAL_SEPARATORS = [".", ","]
_VALID_THOUSANDS_SEPARATORS = [",", ".", ""]
_VALID_FORMATS = [FORMAT_DELIMITED, FORMAT_EXCEL, FORMAT_FIXED, FORMAT_ODS]


@python_2_unicode_compatible
class DataFormat(object):
    """
    General data format of a file describing the basic structure.
    """

    def __init__(self, format_name, location=None):
        if format_name not in (_VALID_FORMATS + ['csv']):
            raise errors.InterfaceError(
                'format is %s but must be on of: %s' % (format_name, _VALID_FORMATS), location)
        else:
            self._location = location
            self._format = format_name if format_name != 'csv' else FORMAT_DELIMITED
            self._header = 0
            self._is_valid = False
            self._allowed_characters = None
            self._encoding = 'cp1252'
            if self.format == FORMAT_DELIMITED:
                self._escape_character = '"'
                self._item_delimiter = ','
                self._quote_character = '"'
                self._skip_initial_space = False
            if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
                self._decimal_separator = ','
                self._line_delimiter = ANY
                self._thousands_separator = ''
            elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
                self._sheet = 1
            if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
                # Valid values for property 'line delimiter', which is only available for delimited and fixed data
                # with no line delimiter only allowed for fixed data.
                self._VALID_LINE_DELIMITER_TEXTS = sorted([
                    line_delimiter_text
                    for line_delimiter, line_delimiter_text in LINE_DELIMITER_TO_TEXT_MAP.items()
                    if (line_delimiter is not None) or (self.format == FORMAT_FIXED)
                ])

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
    def is_valid(self):
        """
        ``True`` if :py:meth:`~DataFormat.validate` has been called and succeeded.

        :rtype: bool
        """
        return self._is_valid

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
        r"""
        Set data format property ``name`` to ``value`` possibly translating ``value`` from
        a human readable representation to an internal one.

        :param str name: any of the ``KEY_*`` constants
        :param value: the value to set the property to as it would show up in a CID. \
            In some cases, the value will be translated to an internal representation. \
            For example ``set_property(KEY_LINE_DELIMITER, 'lf')`` results in \
            :py:attr:`cutplace.data.line_delimiter` being ``'\n'``.
        :type value: str or None

        :raises cutplace.errors.InterfaceError: if ``name`` is not a valid property name for this data format
        :raises cutplace.errors.InterfaceError: if ``value`` is invalid for the specified property
        """
        assert not self.is_valid, 'after validate() has been called property %r cannot be set anymore' % name
        assert name is not None
        assert (value is not None) or name in (KEY_ALLOWED_CHARACTERS, KEY_LINE_DELIMITER)

        name = name.replace(' ', '_')
        property_attribute_name = '_' + name
        if property_attribute_name not in self.__dict__:
            valid_property_names = _tools.human_readable_list(list(self.__dict__.keys()))
            raise errors.InterfaceError(
                'data format property %r for format %s is %r but must be one of %s'
                % (name, self.format, value, valid_property_names), self._location)

        if name == KEY_ENCODING:
            try:
                codecs.lookup(value)
            except LookupError:
                raise errors.InterfaceError(
                    'value for data format property %r is %r but must be a valid encoding'
                    % (KEY_ENCODING, self.encoding), self._location)
            self._encoding = value
        elif name == KEY_HEADER:
            self._header = self._validated_int_at_least_0(name, value)
        elif name == KEY_ALLOWED_CHARACTERS:
            try:
                self._allowed_characters = ranges.Range(value)
            except errors.InterfaceError as error:
                raise errors.InterfaceError(
                    'value for property %r must be a valid range: %s'
                    % (KEY_ALLOWED_CHARACTERS, error), self._location)
        elif name == KEY_DECIMAL_SEPARATOR:
            self._decimal_separator = self._validated_choice(KEY_DECIMAL_SEPARATOR, value, _VALID_DECIMAL_SEPARATORS)
        elif name == KEY_ESCAPE_CHARACTER:
            self._escape_character = self._validated_choice(KEY_ESCAPE_CHARACTER, value, _VALID_ESCAPE_CHARACTERS)
        elif name == KEY_ITEM_DELIMITER:
            self._item_delimiter = self._validated_character(KEY_ITEM_DELIMITER, value)
        elif name == KEY_LINE_DELIMITER:
            try:
                self._line_delimiter = _TEXT_TO_LINE_DELIMITER_MAP[value]
            except KeyError:
                raise errors.InterfaceError(
                    'line delimiter %r must be changed to one of: %s'
                    % (value, _tools.human_readable_list(self._VALID_LINE_DELIMITER_TEXTS)), self._location)
        elif name == KEY_QUOTE_CHARACTER:
            self._quote_character = self._validated_choice(KEY_QUOTE_CHARACTER, value, _VALID_QUOTE_CHARACTERS)
        elif name == KEY_SHEET:
            self._sheet = self._validated_int_at_least_0(name, value)
        elif name == KEY_SKIP_INITIAL_SPACE:
            self._skip_initial_space = self._validated_bool(name, value)
        elif name == KEY_THOUSANDS_SEPARATOR:
            self._thousands_separator = self._validated_choice(
                KEY_DECIMAL_SEPARATOR, value, _VALID_THOUSANDS_SEPARATORS)
        else:
            assert False, 'name=%r' % name

    def _validated_choice(self, key, value, choices, ignore_case=False):
        """
        Same as ``value`` or ``value.lower()`` in case ``ignore_case`` is set
        to ``True``. If the supposed result is not on of the available
        ``choices``, raise `errors.InterfaceError`.
        """
        assert key
        assert value is not None
        assert choices

        result = value if not ignore_case else value.lower()
        if result not in choices:
            raise errors.InterfaceError(
                'data format property %r is %r but must be one of: %s'
                % (key, value, _tools.human_readable_list(choices)), self._location)
        return result

    def _validated_bool(self, key, value):
        assert key
        assert value is not None
        bool_text = self._validated_choice(key, value, ('false', 'true'), True)
        result = (bool_text == 'true')
        return result

    def _validated_int_at_least_0(self, key, value):
        assert key
        assert value is not None
        try:
            result = int(value)
        except ValueError:
            raise errors.InterfaceError(
                'data format property %r is %r but must be a number' % (key, value), self._location)
        if result < 0:
            raise errors.InterfaceError(
                'data format property %r is %d but must be at least 0' % (key, result), self._location)
        return result

    def _validated_character(self, key, value):
        r"""
        A single character intended as value for data format property ``key``
        derived from ``value``, which can be:

        * a decimal or hex number (prefixed with "0x") referring to the ASCII/Unicode of the character
        * a string containing a single character such as "\t".
        * a symbolic name such as "Tab".

        Anything else yields a `InterfaceError`.
        >>> format = DataFormat(FORMAT_DELIMITED)
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
        >>> format._validated_character("x", '\"\\')
        Traceback (most recent call last):
            ...
        InterfaceError: value for data format property 'x' must a number, a single character or
        a symbolic name but is: '"\\'
        >>> format._validated_character("x", '"abc"')
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
            tokens = tokenize.generate_tokens(io.StringIO(value).readline)
            next_token = next(tokens)
            if _tools.is_eof_token(next_token):
                raise errors.InterfaceError(
                    "value for data format property %r must be specified" % key, self._location)
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
                    valid_symbols = _tools.human_readable_list(sorted(errors.NAME_TO_ASCII_CODE_MAP.keys()))
                    raise errors.InterfaceError(
                        'symbolic name %r for data format property %r must be one of: %s'
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
            if not _tools.is_eof_token(next_token):
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
        Validate that property values are consistent.
        """
        assert not self._is_valid, 'validate() must be used only once on data format: %s' % self

        # TODO: Remember locations where properties have been set.
        # TODO: Add see_also_locations for contradicting properties.
        def check_distinct(name1, name2):
            assert name1 is not None
            assert name2 is not None
            assert name1 < name2, 'names must be sorted for consistent error message: %r, %r' % (name1, name2)
            value1 = self.__dict__['_' + name1]
            value2 = self.__dict__['_' + name2]
            if value1 == value2:
                raise errors.InterfaceError(
                    "'%s' and '%s' are both %s but must be different from each other"
                    % (name1, name2, _compat.text_repr(value1)))

        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            check_distinct(KEY_DECIMAL_SEPARATOR, KEY_THOUSANDS_SEPARATOR)
        if self.format == FORMAT_DELIMITED:
            if self.line_delimiter is not None:
                check_distinct(KEY_ESCAPE_CHARACTER, KEY_LINE_DELIMITER)
            check_distinct(KEY_ITEM_DELIMITER, KEY_LINE_DELIMITER)
            check_distinct(KEY_ITEM_DELIMITER, KEY_QUOTE_CHARACTER)
            check_distinct(KEY_LINE_DELIMITER, KEY_QUOTE_CHARACTER)
        self._location = None
        self._is_valid = True

    def __str__(self):
        result = 'DataFormat(%s; ' % self.format
        key_to_value_map = {
            KEY_ALLOWED_CHARACTERS: self.allowed_characters,
            KEY_ENCODING: self.encoding,
            KEY_HEADER: self.header,
        }
        if self.format == FORMAT_DELIMITED:
            key_to_value_map[KEY_ESCAPE_CHARACTER] = self.escape_character
            key_to_value_map[KEY_ITEM_DELIMITER] = self.item_delimiter
            key_to_value_map[KEY_QUOTE_CHARACTER] = self.quote_character
            key_to_value_map[KEY_SKIP_INITIAL_SPACE] = self.skip_initial_space
        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            key_to_value_map[KEY_DECIMAL_SEPARATOR] = self.decimal_separator
            key_to_value_map[KEY_LINE_DELIMITER] = self.line_delimiter
            key_to_value_map[KEY_THOUSANDS_SEPARATOR] = self.thousands_separator
        elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
            key_to_value_map[KEY_SHEET] = self.sheet
        result += ', '.join(
            ['%s=%r' % (key, value) for key, value in sorted(key_to_value_map.items()) if value is not None])
        result += ')'
        return result
