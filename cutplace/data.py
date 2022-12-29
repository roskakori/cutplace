"""
Data formats that describe the general structure of the data.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
import csv
import string
import token
import tokenize

from cutplace import _compat, _tools, errors, ranges
from cutplace._tools import generated_tokens

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
    None: "none",
}
_TEXT_TO_LINE_DELIMITER_MAP = dict([(value, key) for key, value in LINE_DELIMITER_TO_TEXT_MAP.items()])
assert len(LINE_DELIMITER_TO_TEXT_MAP) == len(
    _TEXT_TO_LINE_DELIMITER_MAP
), "values in LINE_DELIMITER_TO_TEXT_MAP must be unique"

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
KEY_FORMAT = "format"
KEY_HEADER = "header"
KEY_ITEM_DELIMITER = "item_delimiter"
KEY_LINE_DELIMITER = "line_delimiter"
KEY_QUOTE_CHARACTER = "quote_character"
KEY_SHEET = "sheet"
KEY_SKIP_INITIAL_SPACE = "skip_initial_space"
KEY_DECIMAL_SEPARATOR = "decimal_separator"
KEY_THOUSANDS_SEPARATOR = "thousands_separator"
KEY_QUOTING = "quoting"

QUOTING_ALL = "all"
QUOTING_MINIMAL = "minimal"

QUOTING_TO_CSV_QUOTE_MAP = {
    QUOTING_ALL: csv.QUOTE_ALL,
    QUOTING_MINIMAL: csv.QUOTE_MINIMAL,
}

_VALID_QUOTE_CHARACTERS = sorted("!\"#$%&'*+-/:;=?\\^_`~")
_VALID_ESCAPE_CHARACTERS = ['"', "\\"]
_VALID_DECIMAL_SEPARATORS = [".", ","]
_VALID_THOUSANDS_SEPARATORS = [",", ".", ""]
_VALID_FORMATS = [FORMAT_DELIMITED, FORMAT_EXCEL, FORMAT_FIXED, FORMAT_ODS]
_VALID_QUOTING = sorted(QUOTING_TO_CSV_QUOTE_MAP.keys())


class DataFormat(object):
    """
    General data format of a file describing the basic structure.
    """

    def __init__(self, format_name, location=None):
        r"""
        Create a new data format.

        :param str format_name: the data format, which must be one of \
            :py:const:`FORMAT_DELIMITED`, :py:const:`FORMAT_EXCEL`,
            :py:const:`FORMAT_FIXED` or :py:const:`FORMAT_ODS`.
        :param cutplace.errors.Location location: location where the data format was declared
        """
        assert format_name == format_name.lower(), "format_name must be lower case: %r" % format_name

        if format_name not in (_VALID_FORMATS + ["csv"]):
            raise errors.InterfaceError(
                "format is %s but must be on of: %s" % (format_name, _VALID_FORMATS),
                location if location is not None else errors.create_caller_location(["data"]),
            )
        # HACK: Treat ``format_name`` 'csv' as synonym for ``FORMAT_DELIMITED``.
        self._format = format_name if format_name != "csv" else FORMAT_DELIMITED
        self._header = 0
        self._is_valid = False
        self._allowed_characters = None
        self._encoding = "cp1252"
        if self.format == FORMAT_DELIMITED:
            self._escape_character = '"'
            self._item_delimiter = ","
            self._quote_character = '"'
            self._quoting = csv.QUOTE_MINIMAL
            self._skip_initial_space = False
        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            self._decimal_separator = "."
            self._line_delimiter = ANY
            self._thousands_separator = ""
        elif self.format in (FORMAT_EXCEL, FORMAT_ODS):
            self._sheet = 1
        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            # Valid values for property 'line delimiter', which is only available for delimited and fixed data
            # with no line delimiter only allowed for fixed data.
            self._VALID_LINE_DELIMITER_TEXTS = sorted(
                line_delimiter_text
                for line_delimiter, line_delimiter_text in LINE_DELIMITER_TO_TEXT_MAP.items()
                if (line_delimiter is not None) or (self.format == FORMAT_FIXED)
            )

    @property
    def format(self):
        return self._format

    @property
    def quoting(self):
        return self._quoting

    @quoting.setter
    def quoting(self, value):
        self._quoting = value

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        assert encoding is not None
        try:
            codecs.lookup(encoding)
        except LookupError:
            assert False, "encoding=%r" % encoding

        self._encoding = encoding

    @property
    def allowed_characters(self):
        return self._allowed_characters

    @allowed_characters.setter
    def allowed_characters(self, new_allowed_characters):
        assert (new_allowed_characters is None) or isinstance(new_allowed_characters, ranges.Range)

        self._allowed_characters = new_allowed_characters

    @property
    def escape_character(self):
        return self._escape_character

    @escape_character.setter
    def escape_character(self, new_escape_character):
        assert self.format == FORMAT_DELIMITED
        assert new_escape_character in _VALID_ESCAPE_CHARACTERS

        self._escape_character = new_escape_character

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, new_header):
        assert new_header >= 0

        self._header = new_header

    @property
    def item_delimiter(self):
        return self._item_delimiter

    @item_delimiter.setter
    def item_delimiter(self, item_delimiter):
        assert self.format == FORMAT_DELIMITED
        assert item_delimiter is not None
        assert len(item_delimiter) == 1
        assert item_delimiter != "\x00", (
            "item delimiter must not be %r (to avoid zero termindated strings in Python's C based CSV reader))"
            % item_delimiter
        )

        self._item_delimiter = item_delimiter

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

    @line_delimiter.setter
    def line_delimiter(self, new_line_delimiter):
        assert self.format in (FORMAT_DELIMITED, FORMAT_FIXED)
        assert new_line_delimiter in LINE_DELIMITER_TO_TEXT_MAP, "new_line_delimiter=%r" % new_line_delimiter
        assert (new_line_delimiter is not None) or (self.format == FORMAT_FIXED), "format=%r" % self.format

        self._line_delimiter = new_line_delimiter

    @property
    def quote_character(self):
        return self._quote_character

    @quote_character.setter
    def quote_character(self, new_quote_character):
        assert self.format in (FORMAT_DELIMITED, FORMAT_FIXED)
        assert new_quote_character in _VALID_QUOTE_CHARACTERS

        self._quote_character = new_quote_character

    @property
    def sheet(self):
        return self._sheet

    @sheet.setter
    def sheet(self, new_sheet):
        assert self.format in (FORMAT_EXCEL, FORMAT_ODS)
        assert new_sheet >= 1

        self._sheet = new_sheet

    @property
    def skip_initial_space(self):
        return self._skip_initial_space

    @skip_initial_space.setter
    def skip_initial_space(self, new_skip_initial_space):
        assert self.format == FORMAT_DELIMITED
        assert new_skip_initial_space in (False, True)

        self._skip_initial_space = new_skip_initial_space

    @property
    def decimal_separator(self):
        return self._decimal_separator

    @decimal_separator.setter
    def decimal_separator(self, new_decimal_separator):
        assert self.format in (FORMAT_DELIMITED, FORMAT_FIXED)
        assert new_decimal_separator in _VALID_DECIMAL_SEPARATORS

        self._decimal_separator = new_decimal_separator

    @property
    def thousands_separator(self):
        return self._thousands_separator

    @thousands_separator.setter
    def thousands_separator(self, new_thousands_separator):
        assert self.format in (FORMAT_DELIMITED, FORMAT_FIXED)
        assert new_thousands_separator in _VALID_THOUSANDS_SEPARATORS

        self._thousands_separator = new_thousands_separator

    def set_property(self, name, value, location=None):
        r"""
        Set data format property ``name`` to ``value`` possibly translating ``value`` from
        a human-readable representation to an internal one.

        :param str name: any of the ``KEY_*`` constants
        :param value: the value to set the property to as it would show up in a CID. \
            In some cases, the value will be translated to an internal representation. \
            For example ``set_property(KEY_LINE_DELIMITER, 'lf')`` results in \
            :py:attr:`cutplace.data.line_delimiter` being ``'\n'``.
        :type location: str or None

        :raises cutplace.errors.InterfaceError: if ``name`` is not a valid property name for this data format
        :raises cutplace.errors.InterfaceError: if ``value`` is invalid for the specified property
        """
        assert not self.is_valid, "after validate() has been called property %r cannot be set anymore" % name
        assert name is not None
        assert name == name.lower(), "property name must be lower case: %r" % name
        assert (value is not None) or (name in (KEY_ALLOWED_CHARACTERS, KEY_LINE_DELIMITER))

        name = name.replace(" ", "_")
        property_attribute_name = "_" + name
        if property_attribute_name not in self.__dict__:
            valid_property_names = _tools.human_readable_list(list(self.__dict__.keys()))
            raise errors.InterfaceError(
                "data format property %s for format %s is %s but must be one of %s"
                % (_compat.text_repr(name), self.format, _compat.text_repr(value), valid_property_names),
                location,
            )

        if name == KEY_ENCODING:
            try:
                codecs.lookup(value)
            except LookupError:
                raise errors.InterfaceError(
                    "value for data format property %s is %s but must be a valid encoding"
                    % (_compat.text_repr(KEY_ENCODING), _compat.text_repr(self.encoding)),
                    location,
                )
            self.encoding = value
        elif name == KEY_HEADER:
            self.header = DataFormat._validated_int_at_least_0(name, value, location)
        elif name == KEY_ALLOWED_CHARACTERS:
            try:
                self._allowed_characters = ranges.Range(value)
            except errors.InterfaceError as error:
                raise errors.InterfaceError(
                    "data format property %s must be a valid range: %s"
                    % (_compat.text_repr(KEY_ALLOWED_CHARACTERS), error),
                    location,
                )
        elif name == KEY_DECIMAL_SEPARATOR:
            self.decimal_separator = DataFormat._validated_choice(
                KEY_DECIMAL_SEPARATOR, value, _VALID_DECIMAL_SEPARATORS, location
            )
        elif name == KEY_ESCAPE_CHARACTER:
            self.escape_character = DataFormat._validated_choice(
                KEY_ESCAPE_CHARACTER, value, _VALID_ESCAPE_CHARACTERS, location
            )
        elif name == KEY_ITEM_DELIMITER:
            item_delimiter = DataFormat._validated_character(KEY_ITEM_DELIMITER, value, location)
            if item_delimiter == "\x00":
                raise errors.InterfaceError(
                    "data format property %s must not be 0 "
                    "(to avoid zero termindated strings in Python's C based CSV reader)"
                    % _compat.text_repr(KEY_ITEM_DELIMITER),
                    location,
                )
            self.item_delimiter = item_delimiter
        elif name == KEY_LINE_DELIMITER:
            try:
                self.line_delimiter = _TEXT_TO_LINE_DELIMITER_MAP[value.lower()]
            except KeyError:
                raise errors.InterfaceError(
                    "line delimiter %s must be changed to one of: %s"
                    % (_compat.text_repr(value), _tools.human_readable_list(self._VALID_LINE_DELIMITER_TEXTS)),
                    location,
                )
        elif name == KEY_QUOTE_CHARACTER:
            self.quote_character = DataFormat._validated_choice(
                KEY_QUOTE_CHARACTER, value, _VALID_QUOTE_CHARACTERS, location
            )
        elif name == KEY_QUOTING:
            quoting = DataFormat._validated_choice(KEY_QUOTING, value, _VALID_QUOTING, location, ignore_case=True)
            self.quoting = QUOTING_TO_CSV_QUOTE_MAP[quoting]
        elif name == KEY_SHEET:
            self.sheet = DataFormat._validated_int_at_least_0(KEY_SHEET, value, location)
        elif name == KEY_SKIP_INITIAL_SPACE:
            self.skip_initial_space = DataFormat._validated_bool(KEY_SKIP_INITIAL_SPACE, value, location)
        elif name == KEY_THOUSANDS_SEPARATOR:
            self.thousands_separator = DataFormat._validated_choice(
                KEY_THOUSANDS_SEPARATOR, value, _VALID_THOUSANDS_SEPARATORS, location
            )
        else:
            assert False, "name=%r" % name

    @staticmethod
    def _validated_choice(key, value, choices, location, ignore_case=False):
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
                "data format property %s is %s but must be one of: %s"
                % (_compat.text_repr(key), _compat.text_repr(value), _tools.human_readable_list(choices)),
                location,
            )
        return result

    @staticmethod
    def _validated_bool(key, value, location):
        assert key
        assert value is not None
        bool_text = DataFormat._validated_choice(key, value.lower(), ("false", "true"), True, location)
        result = bool_text == "true"
        return result

    @staticmethod
    def _validated_int_at_least_0(key, value, location):
        assert key
        assert value is not None
        try:
            result = int(value)
        except ValueError:
            raise errors.InterfaceError(
                "data format property %s is %s but must be a number"
                % (_compat.text_repr(key), _compat.text_repr(value)),
                location,
            )
        if result < 0:
            raise errors.InterfaceError(
                "data format property %s is %d but must be at least 0" % (_compat.text_repr(key), result), location
            )
        return result

    @staticmethod
    def _validated_character(key, value, location):
        r"""
        A single character intended as value for data format property ``key``
        derived from ``value``, which can be:

        * a decimal or hex number (prefixed with ``'0x'``) referring to the ASCII/Unicode of the character
        * a string containing a single character such as ``'\t'``.
        * a symbolic name from :py:const:`cutplace.errors.NAME_TO_ASCII_CODE_MAP` such as ``tab``.

        :raises cutplace.errors.InterfaceError: on any broken ``value``
        """
        assert key
        assert value is not None

        name_for_errors = "data format property %s" % _compat.text_repr(key)
        stripped_value = value.strip()
        if (len(stripped_value) == 1) and (stripped_value not in string.digits):
            result_code = ord(stripped_value)
        else:
            try:
                tokens = generated_tokens(value)
                next_token = next(tokens)
                if _tools.is_eof_token(next_token):
                    raise errors.InterfaceError("value for %s must be specified" % name_for_errors, location)
                next_type = next_token[0]
                next_value = next_token[1]
                if next_type == token.NAME:
                    result_code = ranges.code_for_symbolic_token(name_for_errors, next_value, location)
                elif next_type == token.NUMBER:
                    result_code = ranges.code_for_number_token(name_for_errors, next_value, location)
                elif next_type == token.STRING:
                    result_code = ranges.code_for_string_token(name_for_errors, next_value, location)
                elif (len(next_value) == 1) and not _tools.is_eof_token(next_token):
                    result_code = ord(next_value)
                else:
                    raise errors.InterfaceError(
                        "value for %s must a number, a single character or a symbolic name but is: %s"
                        % (name_for_errors, _compat.text_repr(value)),
                        location,
                    )
                # Ensure there are no further tokens.
                next_token = next(tokens)
                if not _tools.is_eof_token(next_token):
                    raise errors.InterfaceError(
                        "value for %s must be a single character but is: %s"
                        % (name_for_errors, _compat.text_repr(value)),
                        location,
                    )
            except tokenize.TokenError as error:
                raise errors.InterfaceError(
                    "value for %s must be a valid Python token: %s (error: %s)"
                    % (name_for_errors, _compat.text_repr(value), error),
                    location,
                )

        # TODO: Handle 'none' properly.
        assert result_code is not None
        assert result_code >= 0
        result = chr(result_code)
        return result

    def validate(self):
        """
        Validate that property values are consistent.
        """
        assert not self._is_valid, "validate() must be used only once on data format: %s" % self

        # TODO: Remember locations where properties have been set.
        # TODO: Add see_also_locations for contradicting properties.
        def check_distinct(name1, name2):
            assert name1 is not None
            assert name2 is not None
            assert name1 < name2, "names must be sorted for consistent error message: %r, %r" % (name1, name2)
            value1 = self.__dict__["_" + name1]
            value2 = self.__dict__["_" + name2]
            if value1 == value2:
                raise errors.InterfaceError(
                    "'%s' and '%s' are both %s but must be different from each other"
                    % (name1, name2, _compat.text_repr(value1))
                )

        if self.format in (FORMAT_DELIMITED, FORMAT_FIXED):
            check_distinct(KEY_DECIMAL_SEPARATOR, KEY_THOUSANDS_SEPARATOR)
        if self.format == FORMAT_DELIMITED:
            if self.line_delimiter is not None:
                check_distinct(KEY_ESCAPE_CHARACTER, KEY_LINE_DELIMITER)
            check_distinct(KEY_ITEM_DELIMITER, KEY_LINE_DELIMITER)
            check_distinct(KEY_ITEM_DELIMITER, KEY_QUOTE_CHARACTER)
            check_distinct(KEY_LINE_DELIMITER, KEY_QUOTE_CHARACTER)
        self._is_valid = True

    def __str__(self):
        result = "DataFormat(%s; " % self.format
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
        result += ", ".join(
            ["%s=%r" % (key, value) for key, value in sorted(key_to_value_map.items()) if value is not None]
        )
        result += ")"
        return result
