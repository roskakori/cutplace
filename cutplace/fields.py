"""
Standard field formats supported by cutplace.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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

import decimal
import fnmatch
import keyword
import re
import string
import sys
import time

import six

from cutplace import data
from cutplace import ranges
from cutplace import errors
from cutplace import _compat
from cutplace import _tools
from cutplace import sql

from cutplace._compat import python_2_unicode_compatible

# TODO #61: Replace various %r or '%s' by %s and apply _compat.text_repr().

# Expected suffix for classes that describe filed formats.
_FieldFormatClassSuffix = "FieldFormat"

_ASCII_LETTERS = set(string.ascii_letters)
_ASCII_LETTERS_DIGITS_AND_UNDERSCORE = set(string.ascii_letters + string.digits + '_')


@python_2_unicode_compatible
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

    def __init__(self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value=None):
        assert field_name is not None
        assert field_name, 'field_name must not be empty'
        assert is_allowed_to_be_empty in (False, True), 'is_allowed_to_be_empty=%r' % is_allowed_to_be_empty
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

    def validate_characters(self, value):
        """
        Validate that all characters in ``value`` are within
        :py:attr:`~cutplace.data.DataFormat.allowed_characters`.

        :raises cutplace.errors.FieldValueError: if any character in \
          ``value`` is not allowed
        """
        valid_character_range = self.data_format.allowed_characters
        if valid_character_range is not None:
            for character in value:
                try:
                    valid_character_range.validate("character", ord(character))
                except errors.RangeValueError as error:
                    raise errors.FieldValueError(
                        "value for fields '%s' must contain only valid characters: %s" % (self.field_name, error))

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

        if self.length is not None and not (self.is_allowed_to_be_empty and (value == '')):
            try:
                if self.data_format.format == data.FORMAT_FIXED:
                    # Length of fixed format is considered a maximum, fewer characters have to be padded later.
                    value_length = len(value)
                    fixed_length = self.length.lower_limit
                    if value_length > fixed_length:
                        raise errors.FieldValueError(
                            'fixed format field must have at most %d characters instead of %d: %s'
                            % (fixed_length, value_length, _compat.text_repr(value))
                        )
                else:
                    self.length.validate(
                        "length of '%s' with value %s" % (self.field_name, _compat.text_repr(value)), len(value))
            except errors.RangeValueError as error:
                raise errors.FieldValueError(six.text_type(error))

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

    def as_sql(self, db):
        """
        (Work in progress, see https://github.com/roskakori/cutplace/issues/73)
        """
        raise NotImplementedError

    def __str__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.field_name, self.is_allowed_to_be_empty,
                                       self.length, self.rule)


class ChoiceFieldFormat(AbstractFieldFormat):
    """
    Field format accepting only values from a pool of choices.
    """
    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super(ChoiceFieldFormat, self).__init__(
            field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value='')
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
                    "choice value must precede a comma (,) but found: %s" % _compat.text_repr(previous_toky_text))
            choice = _tools.token_text(toky)
            if not choice:
                raise errors.InterfaceError(
                    "choice field must be allowed to be empty instead of containing an empty choice")
            self.choices.append(choice)
            toky = next(tokens)
            if not _tools.is_eof_token(toky):
                if not _tools.is_comma_token(toky):
                    raise errors.InterfaceError(
                        "comma (,) must follow choice value %s but found: %s"
                        % (_compat.text_repr(choice), _compat.text_repr(toky[1])))
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
                % (_compat.text_repr(value), _tools.human_readable_list(self.choices)))
        return value

    def as_sql(self, db):
        return sql.as_sql_text(self._field_name, self._is_allowed_to_be_empty, self._length, self._rule,
                               self._empty_value, db)


class DecimalFieldFormat(AbstractFieldFormat):
    """
    Field format accepting decimal numeric values, taking the data format
    properties :py:const:`cutplace.data.KEY_DECIMAL_SEPARATOR` and
    :py:const:`cutplace.data.KEY_THOUSANDS_SEPARATOR` into account.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value=None):
        super(DecimalFieldFormat, self).__init__(
            field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value)
        if rule.strip() != '':
            raise errors.InterfaceError("decimal rule must be empty")
        self.decimalSeparator = data_format.decimal_separator
        self.thousandsSeparator = data_format.thousands_separator

    def validated_value(self, value):
        assert value

        translated_value = ""
        found_decimal_separator = False
        for valueIndex in range(len(value)):
            character_to_process = value[valueIndex]
            if character_to_process == self.decimalSeparator:
                if found_decimal_separator:
                    raise errors.FieldValueError(
                        "decimal field must contain only one decimal separator (%s): %s"
                        % (_compat.text_repr(self.decimalSeparator), _compat.text_repr(value)))
                translated_value += "."
                found_decimal_separator = True
            elif self.thousandsSeparator and (character_to_process == self.thousandsSeparator):
                if found_decimal_separator:
                    raise errors.FieldValueError(
                        "decimal field must contain thousands separator (%r) only before "
                        "decimal separator (%r): %r (position %d)"
                        % (self.thousandsSeparator, self.decimalSeparator, value, valueIndex + 1))
            else:
                translated_value += character_to_process
        try:
            result = decimal.Decimal(translated_value)
        except Exception as error:
            # TODO: limite exception handler to decimal exception or whatever decimal.Decimal raises.
            message = "value is %r but must be a decimal number: %s" % (value, error)
            raise errors.FieldValueError(message)

        return result


class IntegerFieldFormat(AbstractFieldFormat):
    """
    Field format accepting numeric integer values (without fractional part).
    """
    def __init__(self, field_name, is_allowed_to_be_empty, length_text, rule, data_format, empty_value=None):
        super(IntegerFieldFormat, self).__init__(field_name, is_allowed_to_be_empty, length_text, rule, data_format,
                                                 empty_value)
        # The default range is 32 bit. If the user wants a bigger range, he
        # has to specify it. Python's ``int`` scales to any range as long
        # there is enough memory available to represent it.
        has_length = (length_text is not None) and (length_text.strip() != '')
        has_rule = (rule is not None) and (rule.strip() != '')

        if has_length:
            length = self._length
            if data_format.format == data.FORMAT_FIXED and self._length.lower_limit == self._length.upper_limit:
                length = ranges.Range('1...%d' % self._length.upper_limit)

            length_range = ranges.create_range_from_length(length)

            if length_range.lower_limit == 1:
                self._is_allowed_to_be_empty = False

            if has_rule:
                rule_range = ranges.Range(rule)

                if length_range.upper_limit is not None and rule_range.upper_limit is not None \
                        and length_range.upper_limit < rule_range.upper_limit:
                    raise errors.FieldValueError('length upper limit must be greater than the rule upper limit')

                if length_range.lower_limit is not None and rule_range.lower_limit is not None \
                        and length_range.lower_limit > rule_range.lower_limit:
                    raise errors.FieldValueError('rule lower limit must be less than the length lower limit')

                self.valid_range = rule_range
            else:
                self.valid_range = length_range
        else:
            if has_rule:
                self.valid_range = ranges.Range(rule)
            else:
                self.valid_range = ranges.Range(ranges.DEFAULT_INTEGER_RANGE_TEXT)

    def validated_value(self, value):
        assert value

        try:
            value_as_int = int(value)
        except ValueError:
            raise errors.FieldValueError("value must be an integer number: %s" % _compat.text_repr(value))
        try:
            self.valid_range.validate("value", value_as_int)
        except errors.RangeValueError as error:
            raise errors.FieldValueError(six.text_type(error))
        return value_as_int

    def as_sql(self, db):
        return sql.as_sql_number(self._field_name, self._is_allowed_to_be_empty, self._length, self._rule,
                                 self.valid_range, db)


class DateTimeFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that represent dates or times.
    """
    # We can't use a dictionary here because checks for patterns need to be in order. In
    # particular, "%" need to be checked first, and "YYYY" needs to be checked before "YY".
    _human_readable_to_strptime_map = ["%:%%", "DD:%d", "MM:%m", "YYYY:%Y", "YY:%y", "hh:%H", "mm:%M", "ss:%S"]

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=None):
        super(DateTimeFieldFormat, self).__init__(
            field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)
        self.human_readable_format = rule
        # Create an actual copy of the rule string so `replace()` will not modify the original..
        strptime_format = "".join(rule)

        for patternKeyValue in DateTimeFieldFormat._human_readable_to_strptime_map:
            (key, value) = patternKeyValue.split(":")
            strptime_format = strptime_format.replace(key, value)
        self.strptimeFormat = strptime_format

    def validated_value(self, value):
        assert value

        try:
            result = time.strptime(value, self.strptimeFormat)
        except ValueError:
            raise errors.FieldValueError(
                "date must match format %s (%s) but is: %r (%s)"
                % (self.human_readable_format, self.strptimeFormat, value, sys.exc_info()[1]))
        return result

    def as_sql(self, db):
        return sql.as_sql_date(self._field_name, self._is_allowed_to_be_empty, self.human_readable_format, db)


class RegExFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a specified regular expression.
    """
    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super(RegExFieldFormat, self).__init__(field_name, is_allowed_to_be_empty, length, rule, data_format,
                                               empty_value='')
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)

    def validated_value(self, value):
        assert value

        if not self.regex.match(value):
            raise errors.FieldValueError("value %r must match regular expression: %r" % (value, self.rule))
        return value

    def as_sql(self, db):
        return sql.as_sql_text(self._field_name, self._is_allowed_to_be_empty, self._length, None,
                               self._empty_value, db)


class PatternFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a pattern using "*" and "?" as place holders.
    """
    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=''):
        super(PatternFieldFormat, self).__init__(
            field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)
        self.pattern = fnmatch.translate(rule)
        self.regex = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)

    def validated_value(self, value):
        assert value

        if not self.regex.match(value):
            raise errors.FieldValueError(
                'value %r must match pattern: %r (regex %r)' % (value, self.rule, self.pattern))
        return value

    def as_sql(self, db):
        return sql.as_sql_text(self._field_name, self._is_allowed_to_be_empty, self._length, None,
                               self._empty_value, db)


class TextFieldFormat(AbstractFieldFormat):
    """
    Field format accepting any text.
    """
    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value=''):
        super(TextFieldFormat, self).__init__(
            field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value)

    def validated_value(self, value):
        assert value
        # TODO: Validate Text with rules like: 32..., a...z and so on.
        return value

    def as_sql(self, db):
        return sql.as_sql_text(self._field_name, self._is_allowed_to_be_empty, self._length, None,
                               self._empty_value, db)


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
            'unknown field name %s must be replaced by one of: %s'
            % (_compat.text_repr(field_name_to_look_up), _tools.human_readable_list(available_field_names)),
            location)
    return field_index


def validated_field_name(supposed_field_name, location=None):
    """
    Same as ``supposed_field_name`` except with surrounding white space removed.

    :param cutplace.errors.Location location: location used in case of errors
    :raise cutplace.errors.InterfaceError: if ``supposed_field_name`` is \
      invalid
    """
    field_name = supposed_field_name.strip()
    basic_requirements_text = 'field name must be a valid Python name consisting of ASCII letters, ' \
                              'underscore (_) and digits'
    if field_name == '':
        raise errors.InterfaceError(basic_requirements_text + 'but is empty', location)
    if keyword.iskeyword(field_name):
        raise errors.InterfaceError("field name must not be a Python keyword but is: '%s'" % field_name, location)
    is_first_character = True
    for character in field_name:
        if is_first_character:
            if character not in _ASCII_LETTERS:
                raise errors.InterfaceError(
                    "field name must begin with a lower-case letter but is: %s"
                    % _compat.text_repr(field_name), location)
            is_first_character = False
        else:
            if character not in _ASCII_LETTERS_DIGITS_AND_UNDERSCORE:
                raise errors.InterfaceError(
                    basic_requirements_text + 'but is: %s' % _compat.text_repr(field_name), location)
    return field_name
