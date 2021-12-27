"""
Standard field formats supported by cutplace.
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
import decimal
import fnmatch
import keyword
import re
import string
import sys
import time
from typing import Any, Optional

from cutplace import _compat, _tools, data, errors, ranges

# TODO #61: Replace various %r or '%s' by %s and apply _compat.text_repr().

# Expected suffix for classes that describe filed formats.
_FieldFormatClassSuffix = "FieldFormat"

_ASCII_LETTERS = set(string.ascii_letters)
_ASCII_LETTERS_DIGITS_AND_UNDERSCORE = set(string.ascii_letters + string.digits + "_")


class AbstractFieldFormat(object):
    """
    Abstract format description of a field in a data file, acting base for all
    other field formats. To implement another field format, it is usually
    sufficient to:

      1. Overload :py:meth:`~cutplace.fields.AbstractFieldFormat.__init__()`
         but call ``super().__init__(...)`` from it.
      2. Implement
         :py:meth:`~cutplace.fields.AbstractFieldFormat.validated_value()`.
    """

    def __init__(
        self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value: Optional[Any] = None
    ):
        assert field_name is not None
        assert field_name, "field_name must not be empty"
        assert is_allowed_to_be_empty in (False, True), "is_allowed_to_be_empty=%r" % is_allowed_to_be_empty
        assert rule is not None, 'to specify "no rule" use "" instead of None'
        assert data_format is not None
        # TODO #82: Cleanup validation for declared field formats.

        self._field_name = field_name
        self._is_allowed_to_be_empty = is_allowed_to_be_empty
        self._length = ranges.Range(length_text)
        self._rule = rule
        self._data_format = data_format
        self._empty_value = empty_value
        self._example = None

    @property
    def field_name(self):
        """
        The name of the field.
        """
        return self._field_name

    @property
    def is_allowed_to_be_empty(self):
        """
        ``True`` if the field can be empty in the data set, resulting in
        :py:meth:`~cutplace.fields.AbstractFieldFormat.validated()` to return
        :py:attr:`~cutplace.fields.AbstractFieldFormat.empty_value`.

        :rtype: bool
        """
        return self._is_allowed_to_be_empty

    @property
    def length(self):
        """
        A :py:class:`cutplace.ranges.Range` describing the possible length of
        the value.
        """
        return self._length

    @property
    def rule(self):
        """
        A field format dependent rule to describe possible values.

        :rtype: str
        """
        return self._rule

    @property
    def data_format(self):
        """
        The :py:class:`cutplace.data.DataFormat` the data set has in case the
        field needs any properties from it to validate its value, for
        instance :py:const:`cutplace.data.KEY_DECIMAL_SEPARATOR`.
        """
        return self._data_format

    @property
    def empty_value(self):
        """
        The result of
        :py:meth:`~cutplace.fields.AbstractFieldFormat.validated()` in case
        the ``value`` passed to it is an empty string.

        :rtype: same type as a typical result of \
          :py:meth:`~cutplace.fields.AbstractFieldFormat.validated()`
        """
        return self._empty_value

    def _get__example(self):
        return self._example

    def _set_example(self, new_example):
        if new_example is not None:
            self.validated(new_example)
        self._example = new_example

    example = property(_get__example, _set_example, doc="Example value or ``None`` if no example is provided.")

    def sql_ansi_type(self):
        """
        A tuple describing the ANSI SQL type and it size, which has to be one
        of the following variants:

        * ``('char', length)``: a string with a fixed amount of characters
          with ``length`` indicating the number of characters.
        * ``('datetime',)``: a date and/or time.
        * ``('decimal', scale, precision)``: a decimal number.
        * ``('varchar', length)``: a string with a variable amount of
          characters with ``length`` indicating the number of characters.

        The only required part of the tuple is the first item (the ANSI SQL
        type name). If the others are omitted, reasonable defaults are used.

        The default implementation is ``'varchar'`` with a maximum number of
        characters derived from
        :py:attr:`~cutplace.fields.AbstractFieldFormat.length`.
        """
        return ("varchar", None if self.length is None else self.length.upper_limit)

    def validate_characters(self, value):
        """
        Validate that all characters in ``value`` are within
        :py:attr:`~cutplace.data.DataFormat.allowed_characters`.

        :raises cutplace.errors.FieldValueError: if any character in \
          ``value`` is not allowed
        """
        valid_character_range = self.data_format.allowed_characters
        if valid_character_range is not None:
            for character_column, character in enumerate(value, 1):
                character_code = ord(character)
                try:
                    valid_character_range.validate("character", character_code)
                except errors.RangeValueError:
                    raise errors.FieldValueError(
                        "character %s (code point U+%04x, decimal %d) in field '%s' at column %d must be an allowed "
                        "character: %s"
                        % (
                            _compat.text_repr(character),
                            character_code,
                            character_code,
                            self.field_name,
                            character_column,
                            valid_character_range,
                        )
                    )

    def validate_empty(self, value):
        """
        Validate that ``value`` actually is not empty in case
        :py:attr:`~cutplace.fields.AbstractFieldFormat.is_allowed_to_be_empty`
        is ``True``.

        :raises cutplace.errors.FieldValueError: if ``value`` is empty but \
          must not be
        """
        if not self.is_allowed_to_be_empty:
            if not value:
                raise errors.FieldValueError("value must not be empty")

    def validate_length(self, value):
        """
        Validate that ``value`` conforms to
        :py:attr:`~cutplace.fields.AbstractFieldFormat.length`.

        :raises cutplace.errors.FieldValueError: if ``value`` is too short \
          or too long
        """
        assert value is not None

        if self.length is not None and not (self.is_allowed_to_be_empty and (value == "")):
            try:
                if self.data_format.format == data.FORMAT_FIXED:
                    # Length of fixed format is considered a maximum, fewer characters have to be padded later.
                    value_length = len(value)
                    fixed_length = self.length.lower_limit
                    if value_length > fixed_length:
                        raise errors.FieldValueError(
                            "fixed format field must have at most %d characters instead of %d: %s"
                            % (fixed_length, value_length, _compat.text_repr(value))
                        )
                else:
                    self.length.validate(
                        "length of '%s' with value %s" % (self.field_name, _compat.text_repr(value)), len(value)
                    )
            except errors.RangeValueError as error:
                raise errors.FieldValueError(str(error))

    def validated_value(self, value):
        """
        The ``value`` in its native type for this field.

        By the time this is called it is already ensured that:

          - ``value`` is not an empty string
          - ``value`` contains only valid characters
          - trailing blanks have been removed from ``value`` for fixed format
            data

        Concrete field formats must override this because the default
        implementation just raises a :py:exc:`~builtins.NotImplementedError`.
        """
        assert value

        raise NotImplementedError()

    def validated(self, value):
        """
        Validate that value complies with field description and return the value in its "native"
        type.

        :raises cutplace.errors.FieldValueError: if ``value`` is invalid
        """
        self.validate_characters(value)
        self.validate_empty(value)
        self.validate_length(value)
        if self.data_format.format == data.FORMAT_FIXED:
            possibly_stripped_value = value.strip()
        else:
            possibly_stripped_value = value
        if possibly_stripped_value:
            result = self.validated_value(possibly_stripped_value)
        else:
            result = self.empty_value
        return result

    def __str__(self):
        return "%s(%s, %s, %s, %s)" % (
            self.__class__.__name__,
            _compat.text_repr(self.field_name),
            self.is_allowed_to_be_empty,
            _compat.text_repr(self.length),
            _compat.text_repr(self.rule),
        )


class ChoiceFieldFormat(AbstractFieldFormat):
    """
    Field format accepting only values from a pool of choices.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value="")
        self.choices = []

        # Split rule into tokens, ignoring white space.
        tokens = _tools.tokenize_without_space(rule)

        # Extract choices from rule tokens.
        previous_toky = None
        toky = next(tokens)
        while not _tools.is_eof_token(toky):
            if _tools.is_comma_token(toky):
                # Handle comma after comma without choice.
                if previous_toky:
                    previous_toky_text = previous_toky[1]
                else:
                    previous_toky_text = None
                raise errors.InterfaceError(
                    "choice value must precede a comma (,) but found: %s" % _compat.text_repr(previous_toky_text)
                )
            choice = _tools.token_text(toky)
            if not choice:
                raise errors.InterfaceError(
                    "choice field must be allowed to be empty instead of containing an empty choice"
                )
            self.choices.append(choice)
            toky = next(tokens)
            if not _tools.is_eof_token(toky):
                if not _tools.is_comma_token(toky):
                    raise errors.InterfaceError(
                        "comma (,) must follow choice value %s but found: %s"
                        % (_compat.text_repr(choice), _compat.text_repr(toky[1]))
                    )
                # Process next choice after comma.
                toky = next(tokens)
                if _tools.is_eof_token(toky):
                    raise errors.InterfaceError("trailing comma (,) must be removed")
        if not self.is_allowed_to_be_empty and not self.choices:
            raise errors.InterfaceError("choice field without any choices must be allowed to be empty")

    def validated_value(self, value):
        assert value

        if value not in self.choices:
            raise errors.FieldValueError(
                "value is %s but must be one of: %s"
                % (_compat.text_repr(value), _tools.human_readable_list(self.choices))
            )
        return value


class ConstantFieldFormat(AbstractFieldFormat):
    """
    Field format accepting only values from a pool of choices.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value="")

        # Extract constant from rule tokens.
        tokens = _tools.tokenize_without_space(rule)
        toky = next(tokens)
        if _tools.is_eof_token(toky):
            # No rule means that the field must always be empty.
            self._constant = ""
        else:
            self._constant = _tools.token_text(toky)
            toky = next(tokens)
            if not _tools.is_eof_token(toky):
                raise errors.InterfaceError(
                    "constant rule must be a single Python token but also found: %s"
                    % _compat.text_repr(_tools.token_text(toky))
                )
        has_empty_rule = rule == ""
        if self.is_allowed_to_be_empty and not has_empty_rule:
            raise errors.InterfaceError(
                "to describe a Constant that can be empty, use a Choice field with a single choice"
            )
        if not self.is_allowed_to_be_empty and has_empty_rule:
            raise errors.InterfaceError("field must be marked as empty to describe a constant empty value")
        try:
            self.length.validate("rule of constant field %s" % _compat.text_repr(self.field_name), len(self._constant))
        except errors.RangeValueError:
            raise errors.InterfaceError(
                "length is %s but must be %d to match constant %s"
                % (self.length, len(self._constant), _compat.text_repr(self._constant))
            )

    def validated_value(self, value):
        assert value

        if value != self._constant:
            raise errors.FieldValueError(
                "value is %s but must be constant: %s" % (_compat.text_repr(value), _compat.text_repr(self._constant))
            )
        return value


class DecimalFieldFormat(AbstractFieldFormat):
    """
    Field format accepting decimal numeric values, taking the data format
    properties :py:const:`cutplace.data.KEY_DECIMAL_SEPARATOR` and
    :py:const:`cutplace.data.KEY_THOUSANDS_SEPARATOR` into account.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value=None):
        super().__init__(field_name, is_allowed_to_be_empty, "", "", data_format, empty_value)
        assert rule is not None, 'to specify "no rule" use "" instead of None'
        self.decimal_separator = data_format.decimal_separator
        self.thousands_separator = data_format.thousands_separator
        self.valid_range = ranges.DecimalRange(rule, ranges.DEFAULT_DECIMAL_RANGE_TEXT)
        self._length = ranges.DecimalRange(length_text)

        self._precision = self.valid_range.precision
        self._scale = self.valid_range.scale

    def sql_ansi_type(self):
        return ("decimal", self._scale, self._precision)

    def validated_value(self, value):
        assert value

        translated_value = ""
        found_decimal_separator = False
        for character_to_process in value:
            if character_to_process == self.decimal_separator:
                if found_decimal_separator:
                    raise errors.FieldValueError(
                        "decimal field must contain only one decimal separator (%s): %s"
                        % (_compat.text_repr(self.decimal_separator), _compat.text_repr(value))
                    )
                translated_value += "."
                found_decimal_separator = True
            elif self.thousands_separator and (character_to_process == self.thousands_separator):
                if found_decimal_separator:
                    raise errors.FieldValueError(
                        "decimal field must contain thousands separator (%r) only before "
                        "decimal separator (%r): %r " % (self.thousands_separator, self.decimal_separator, value)
                    )
            else:
                translated_value += character_to_process

        try:
            result = decimal.Decimal(translated_value)
        except Exception as error:
            # TODO: limit exception handler to decimal exception or whatever decimal.Decimal raises.
            message = "value is %r but must be a decimal number: %s" % (value, error)
            raise errors.FieldValueError(message)

        try:
            self.valid_range.validate(self._field_name, result)
        except errors.RangeValueError as error:
            raise errors.FieldValueError(str(error))

        return result


class IntegerFieldFormat(AbstractFieldFormat):
    """
    Field format accepting numeric integer values (without fractional part).
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value=None):
        super().__init__(field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value)

        is_fixed_format = data_format.format == data.FORMAT_FIXED
        has_length = (length_text is not None) and (length_text.strip() != "")
        if has_length:
            length = self.length
            if is_fixed_format:
                # For fixed data format, use an implicit range starting from
                # 1 to take into account that leading and trailing blanks
                # might be missing from the rule parts.
                assert self.length.lower_limit == self.length.upper_limit
                length = ranges.Range("1...%d" % self.length.upper_limit)
            length_range = ranges.create_range_from_length(length)

        has_rule = (rule is not None) and (rule.strip() != "")
        if has_rule:
            rule_range = ranges.Range(rule)

        if has_length:
            if has_rule:
                # Both a length and a rule have been specified: check if all
                # non ``None`` parts of each item of the rule fit within the
                # range of the length. Then use the rule as valid range.
                for rule_item in rule_range.items:
                    partial_rule_limits = [
                        partial_rule_limit for partial_rule_limit in rule_item if partial_rule_limit is not None
                    ]
                    for partial_rule_limit in partial_rule_limits:
                        length_of_partial_rule_limit = _tools.length_of_int(partial_rule_limit)
                        try:
                            length.validate(
                                "length of partial rule limit '%d'" % partial_rule_limit, length_of_partial_rule_limit
                            )
                        except errors.RangeValueError as error:
                            message = "length must be consistent with rule: %s" % error
                            raise errors.InterfaceError(message)
                self.valid_range = rule_range
            else:
                # A length but no rule has been specified: derive a valid
                # range from the length.
                self.valid_range = length_range
        else:
            if has_rule:
                # No length but a rule has been specified: use the rule as
                # valid range.
                self.valid_range = rule_range
            else:
                # No length and no rule has been specified: use a default
                # range of signed 32 bit integer. If the user wants a bigger
                # range, he has to specify it. Python's ``int`` scales to any
                # range as long as there is enough memory available to
                # represent it.
                self.valid_range = ranges.Range(ranges.DEFAULT_INTEGER_RANGE_TEXT)

    def sql_ansi_type(self):
        def sign_adjusted_limit(limit):
            """
            Similar to ``abs(limit)`` but increases negative values by 1 so
            negative boundary values like -32768 result in the same amount of
            bytes like to corresponding positive value 32767.
            """
            assert limit is not None
            if limit >= 0:
                result = limit
            else:
                result = -(limit + 1)
            return result

        if self.valid_range is None:
            limit = None
        else:
            lower_limit = self.valid_range.lower_limit
            upper_limit = self.valid_range.upper_limit
            limit = max(sign_adjusted_limit(lower_limit), sign_adjusted_limit(upper_limit))
        return "int", limit

    def validated_value(self, value):
        assert value

        try:
            value_as_int = int(value)
        except ValueError:
            raise errors.FieldValueError("value must be an integer number: %s" % _compat.text_repr(value))
        try:
            self.valid_range.validate("value", value_as_int)
        except errors.RangeValueError as error:
            raise errors.FieldValueError(str(error))
        return value_as_int


class DateTimeFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that represent dates or times.
    """

    # We can't use a dictionary here because checks for patterns need to be in order. In
    # particular, "%" need to be checked first, and "YYYY" needs to be checked before "YY".
    _HUMAN_READABLE_TO_STRPTIME_TUPLES = (
        ("%", "%%"),
        ("DD", "%d"),
        ("MM", "%m"),
        ("YYYY", "%Y"),
        ("YY", "%y"),
        ("hh", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    )
    _STRPTIME_TIME_DIRECTIVES = ("%H", "%M", "%S")
    _STRPTIME_DATE_DIRECTIVES = ("%d", "%m", "%y", "%Y")
    _NO_EXCEL_TIME = " 00:00:00"
    _NO_EXCEL_TIME_LENGTH = len(_NO_EXCEL_TIME)

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=None):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)
        self.human_readable_format = rule

        self.strptime_format = rule
        for human_readyble_item, strptime_item in DateTimeFieldFormat._HUMAN_READABLE_TO_STRPTIME_TUPLES:
            self.strptime_format = self.strptime_format.replace(human_readyble_item, strptime_item)
        self._has_time = any(
            directive in self.strptime_format for directive in DateTimeFieldFormat._STRPTIME_TIME_DIRECTIVES
        )
        self._has_date = any(
            directive in self.strptime_format for directive in DateTimeFieldFormat._STRPTIME_DATE_DIRECTIVES
        )

    def sql_ansi_type(self):
        # FIXME: Use timestamp for ANSI, date, datetime and time for others.
        return ("date",)

    def validated_value(self, value):
        assert value

        if (
            not self._has_time
            and (self.data_format.format == data.FORMAT_EXCEL)
            and (value.endswith(DateTimeFieldFormat._NO_EXCEL_TIME))
        ):
            value_to_validate = value[: -DateTimeFieldFormat._NO_EXCEL_TIME_LENGTH]
        else:
            value_to_validate = value

        try:
            result = time.strptime(value_to_validate, self.strptime_format)
        except ValueError:
            raise errors.FieldValueError(
                "date must match format %s (%s) but is: %s (%s)"
                % (
                    self.human_readable_format,
                    self.strptime_format,
                    _compat.text_repr(value_to_validate),
                    sys.exc_info()[1],
                )
            )
        return result


class RegExFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a specified regular expression.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value="")
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)

    def validated_value(self, value):
        assert value

        if not self.regex.match(value):
            raise errors.FieldValueError(
                "value %s must match regular expression: %s" % (_compat.text_repr(value), _compat.text_repr(self.rule))
            )
        return value


class PatternFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a pattern using "*" and "?" as place holders.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=""):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)
        self.pattern = fnmatch.translate(rule)
        self.regex = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)

    def validated_value(self, value):
        assert value

        if not self.regex.match(value):
            raise errors.FieldValueError(
                "value %s must match pattern: %s (regex %s)"
                % (_compat.text_repr(value), _compat.text_repr(self.rule), _compat.text_repr(self.pattern))
            )
        return value


class TextFieldFormat(AbstractFieldFormat):
    """
    Field format accepting any text.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=""):
        super().__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)

    def validated_value(self, value):
        assert value
        # TODO: Validate Text with rules like: 32..., a...z and so on.
        return value


def field_name_index(field_name_to_look_up, available_field_names, location):
    """
    The index of ``field_name_to_look_up`` (without leading or trailing
    white space) in ``available_field_names``.

    :param cutplace.errors.Location location: location used in case of errors
    :raise cutplace.errors.InterfaceError: if ``field_name_to_look_up`` is \
      not part of ``available_field_names``
    """
    assert field_name_to_look_up is not None
    assert field_name_to_look_up == field_name_to_look_up.strip()
    assert available_field_names

    field_name_to_look_up = field_name_to_look_up.strip()
    try:
        field_index = available_field_names.index(field_name_to_look_up)
    except ValueError:
        raise errors.InterfaceError(
            "unknown field name %s must be replaced by one of: %s"
            % (_compat.text_repr(field_name_to_look_up), _tools.human_readable_list(available_field_names)),
            location,
        )
    return field_index


def validated_field_name(supposed_field_name, location=None):
    """
    Same as ``supposed_field_name`` except with surrounding white space removed.

    :param cutplace.errors.Location location: location used in case of errors
    :raise cutplace.errors.InterfaceError: if ``supposed_field_name`` is \
      invalid
    """
    field_name = supposed_field_name.strip()
    basic_requirements_text = (
        "field name must be a valid Python name consisting of ASCII letters, " "underscore (_) and digits"
    )
    if field_name == "":
        raise errors.InterfaceError(basic_requirements_text + "but is empty", location)
    if keyword.iskeyword(field_name):
        raise errors.InterfaceError("field name must not be a Python keyword but is: '%s'" % field_name, location)
    is_first_character = True
    for character in field_name:
        if is_first_character:
            if character not in _ASCII_LETTERS:
                raise errors.InterfaceError(
                    "field name must begin with a lower-case letter but is: %s" % _compat.text_repr(field_name),
                    location,
                )
            is_first_character = False
        else:
            if character not in _ASCII_LETTERS_DIGITS_AND_UNDERSCORE:
                raise errors.InterfaceError(
                    basic_requirements_text + "but is: %s" % _compat.text_repr(field_name), location
                )
    return field_name
