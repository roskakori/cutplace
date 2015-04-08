# -*- coding: iso-8859-15 -*-
"""
Tests  for field formats.
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
import logging
import unittest

import six

from cutplace import data
from cutplace import errors
from cutplace import fields

from tests import dev_test

_ANY_FORMAT = data.DataFormat(data.FORMAT_DELIMITED)
_FIXED_FORMAT = data.DataFormat(data.FORMAT_FIXED)


def _create_german_decimal_format():
    german_format = data.DataFormat(data.FORMAT_DELIMITED)
    german_format.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
    german_format.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
    result = fields.DecimalFieldFormat("x", False, None, "", german_format)
    return result


class AbstractFieldFormatTest(unittest.TestCase):
    """
    Test for base validation in `AbstractFieldFormatTest`.
    """

    def test_can_accept_empty_value_for_field_allowed_to_be_empty(self):
        field_format = fields.AbstractFieldFormat("x", True, None, "", _ANY_FORMAT)
        field_format.validate_empty("")

    def test_can_reject_empty_value_for_field_not_allowed_to_be_empty(self):
        field_format = fields.AbstractFieldFormat("x", False, None, "", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validate_empty, "")

    def test_can_validate_length(self):
        field_format = fields.AbstractFieldFormat("x", False, "3...5", "", _ANY_FORMAT)
        field_format.validate_length("123")
        field_format.validate_length("1234")
        field_format.validate_length("12345")

    def test_fails_on_validation_of_broken_length(self):
        field_format = fields.AbstractFieldFormat('x', False, '3...5', '', _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validate_length, '12')
        self.assertRaises(errors.FieldValueError, field_format.validate_length, '123456')

    def test_can_create_empty_field_with_length_limit(self):
        field_format = fields.AbstractFieldFormat("x", True, "3...5", "", _ANY_FORMAT)
        field_format.validate_length("")

    def test_can_clear_example(self):
        field_format = fields.AbstractFieldFormat('x', False, '3...5', '', _ANY_FORMAT)
        field_format.example = None

    def test_fails_on_invalid_character(self):
        data_format = data.DataFormat(data.FORMAT_DELIMITED)
        data_format.set_property(data.KEY_ALLOWED_CHARACTERS, '"a"..."c"')
        field_format = fields.AbstractFieldFormat('something', False, '3...5', '', data_format)
        field_format.validate_characters('cba')
        dev_test.assert_raises_and_fnmatches(
            self, errors.FieldValueError,
            "character 'x' (code point U+0078, decimal 120) in field 'something' at column 3 "
            + "must be an allowed character: 97...99",
            field_format.validate_characters, 'abxba'
        )

    def test_can_raise_not_implemented_error(self):
        field_format = fields.AbstractFieldFormat('x', False, '3...5', '', _ANY_FORMAT)
        self.assertRaises(NotImplementedError, field_format.validated_value, 4)

    def test_can_output_field_format_as_string(self):
        field_format = fields.AbstractFieldFormat('x', False, '3...5', '', _ANY_FORMAT)
        self.assertEqual(six.text_type(field_format), "AbstractFieldFormat('x', False, Range('3...5'), '')")


class DateTimeFieldFormatTest(unittest.TestCase):
    """
    Tests  for `DateTimeFieldFormat`.
    """
    def test_can_accept_valid_dates(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _ANY_FORMAT)
        field_format.validated("2000-01-01")
        field_format.validated("2000-02-29")
        field_format.validated("1955-02-28")
        field_format.validated("2345-12-31")
        field_format.validated("0001-01-01")
        field_format.validated("9999-12-31")

    def test_can_accept_empty_date(self):
        field_format = fields.DateTimeFieldFormat("x", True, None, "YYYY-MM-DD", _ANY_FORMAT)
        self.assertEqual(field_format.validated(""), None)
        self.assertNotEquals(field_format.validated("2000-01-01"), None)

    def test_fails_on_broken_dates(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "2000-02-30")
        self.assertRaises(errors.FieldValueError, field_format.validated, "0000-01-01")
        self.assertRaises(errors.FieldValueError, field_format.validated, "this is a bad day")

        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        field_format.validated("2000-1-1")

    def test_can_handle_rule_with_percent_sign(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "%YYYY-MM-DD", _ANY_FORMAT)
        field_format.validated("%2000-01-01")


class DecimalFieldFormatTest(unittest.TestCase):
    """
    Test for `DecimalFieldFormat`.
    """
    def test_can_validate_decimals(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "", _ANY_FORMAT)
        self.assertEqual(decimal.Decimal("17.23"), field_format.validated("17.23"))
        self.assertEqual(decimal.Decimal("17.123456789"), field_format.validated("17.123456789"))

    def test_can_validate_german_decimals(self):
        german_data_format = data.DataFormat(data.FORMAT_DELIMITED)
        german_data_format.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
        german_data_format.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
        german_decimal_field_format = _create_german_decimal_format()
        self.assertEqual(decimal.Decimal("17.23"), german_decimal_field_format.validated("17,23"))
        self.assertEqual(decimal.Decimal("12345678"), german_decimal_field_format.validated("12.345.678"))
        self.assertEqual(decimal.Decimal("171234567.89"), german_decimal_field_format.validated("171.234.567,89"))

    def test_can_validate_rule_for_field_format(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...4.2", _ANY_FORMAT)
        self.assertEqual(decimal.Decimal('3.2'), field_format.validated('3.2'))
        self.assertEqual(decimal.Decimal('3.5'), field_format.validated('3.5'))
        self.assertEqual(decimal.Decimal('4.2'), field_format.validated('4.2'))

        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...", _ANY_FORMAT)
        self.assertEqual(decimal.Decimal('3.2'), field_format.validated('3.2'))
        self.assertEqual(decimal.Decimal('3.5'), field_format.validated('3.5'))
        self.assertEqual(decimal.Decimal('333.5'), field_format.validated('333.5'))

        field_format = fields.DecimalFieldFormat("x", False, None, "...4.2", _ANY_FORMAT)
        self.assertEqual(decimal.Decimal('4.2'), field_format.validated('4.2'))
        self.assertEqual(decimal.Decimal('-333.5'), field_format.validated('-333.5'))

    def test_fails_on_outer_range_for_field_rule(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...4.2", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, '4.3')
        self.assertRaises(errors.FieldValueError, field_format.validated, '3.1')

        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, '3.1')

        field_format = fields.DecimalFieldFormat("x", False, None, "...4.2", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, '4.3')

    def test_fails_on_no_numeric_value(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...4.2", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "abc")

    def test_fails_on_double_decimal_separator(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "3.2...4.2", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "3..3")

    def test_fails_on_thousand_separator_after_decimal_separator(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "3000.2...4000.2", _ANY_FORMAT)
        field_format.thousands_separator = "."
        field_format.decimal_separator = ","
        self.assertRaises(errors.FieldValueError, field_format.validated, "3000,300.234")

    def test_can_use_default_rule(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "", _ANY_FORMAT)
        self.assertEqual(field_format.valid_range.upper_limit, decimal.Decimal('9999999999999999999.999999999999'))
        self.assertEqual(field_format.valid_range.lower_limit, decimal.Decimal('-9999999999999999999.999999999999'))


class IntegerFieldFormatTest(unittest.TestCase):
    """
    Tests  for py:class:`cutplace.fields.IntegerFieldFormat`.
    """
    def test_can_set_default_range_without_rule(self):
        field_format = fields.IntegerFieldFormat("x", False, None, '', _ANY_FORMAT)
        self.assertEqual(field_format.valid_range.items, [(-2147483648, 2147483647)])

    def test_can_set_range_from_rule(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...5", _ANY_FORMAT)
        self.assertEqual(field_format.valid_range.items, [(1, 5)])

    def test_can_validate_field_with_range(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...10", _ANY_FORMAT)
        self.assertEqual(field_format.validated("1"), 1)
        self.assertEqual(field_format.validated("7"), 7)
        self.assertEqual(field_format.validated("10"), 10)
        field_format = fields.IntegerFieldFormat("x", False, None, "123", _ANY_FORMAT)
        self.assertEqual(field_format.validated("123"), 123)

    def test_can_set_range_from_length(self):
        field_format = fields.IntegerFieldFormat("x", False, "1...3", '', _ANY_FORMAT)
        self.assertEqual(field_format.valid_range.items, [(-99, 999)])

    def test_can_validate_field_with_range_from_length(self):
        field_format = fields.IntegerFieldFormat("x", False, "2...2", "", _ANY_FORMAT)
        self.assertEqual(field_format.validated("-9"), -9)
        self.assertEqual(field_format.validated("-1"), -1)
        self.assertEqual(field_format.validated("10"), 10)
        self.assertEqual(field_format.validated("99"), 99)
        self.assertRaises(errors.FieldValueError, field_format.validated, "0")
        self.assertRaises(errors.FieldValueError, field_format.validated, "9")
        self.assertRaises(errors.FieldValueError, field_format.validated, "-10")
        self.assertRaises(errors.FieldValueError, field_format.validated, "100")

        field_format = fields.IntegerFieldFormat("x", False, "3...4, 10...", "", _ANY_FORMAT)
        self.assertEqual(field_format.validated("-999"), -999)
        self.assertEqual(field_format.validated("-10"), -10)
        self.assertEqual(field_format.validated("100"), 100)
        self.assertEqual(field_format.validated("9999"), 9999)
        self.assertRaises(errors.FieldValueError, field_format.validated, "-1")
        self.assertRaises(errors.FieldValueError, field_format.validated, "9")
        self.assertRaises(errors.FieldValueError, field_format.validated, "10000")

    def test_can_validate_empty_value_with_range_from_length(self):
        field_format = fields.IntegerFieldFormat('x', True, '2...3, 5...', '', _ANY_FORMAT)
        self.assertEqual(field_format.validated('10'), 10)
        self.assertEqual(field_format.validated('10000'), 10000)
        self.assertEqual(field_format.validated(''), None)
        self.assertRaises(errors.FieldValueError, field_format.validated, '1')

    def test_can_validate_fixed_format_with_length_and_rule(self):
        field_format = fields.IntegerFieldFormat('x', False, '3', '12...789', _FIXED_FORMAT)
        self.assertEqual(field_format.validated('100'), 100)
        self.assertEqual(field_format.validated('12'), 12)
        self.assertEqual(field_format.validated(' 12'), 12)
        self.assertEqual(field_format.validated('12 '), 12)
        self.assertEqual(field_format.validated('012'), 12)

    def test_fails_on_inconsistent_fixed_length_and_rule(self):
        dev_test.assert_raises_and_fnmatches(
            self, errors.InterfaceError,
            "length must be consistent with rule: "
            "length of partial rule limit '1234' is 4 but must be within range: 1...3",
            fields.IntegerFieldFormat, 'x', False, '3', '...1234', _FIXED_FORMAT
        )
        dev_test.assert_raises_and_fnmatches(
            self, errors.InterfaceError,
            "length must be consistent with rule: "
            "length of partial rule limit '1234' is 4 but must be within range: 1...3",
            fields.IntegerFieldFormat, 'x', False, '3', '123...456, 1234...', _FIXED_FORMAT
        )

    def test_can_set_range_from_length_or_rule(self):
        field_format = fields.IntegerFieldFormat("x", False, "1...", "3...5", _ANY_FORMAT)
        self.assertEqual(field_format.validated("3"), 3)
        self.assertEqual(field_format.validated("5"), 5)
        self.assertRaises(errors.FieldValueError, field_format.validated, "2")
        self.assertRaises(errors.FieldValueError, field_format.validated, "6")

        field_format = fields.IntegerFieldFormat("x", False, "1...5", "-9...-1, 10...", _ANY_FORMAT)
        self.assertEqual(field_format.validated("-1"), -1)
        self.assertEqual(field_format.validated("-9"), -9)
        self.assertEqual(field_format.validated("10"), 10)
        self.assertRaises(errors.FieldValueError, field_format.validated, "-10")
        self.assertRaises(errors.FieldValueError, field_format.validated, "0")
        self.assertRaises(errors.FieldValueError, field_format.validated, "9")

    def test_fails_on_inconsistent_length_and_rule(self):
        self.assertRaises(errors.InterfaceError, fields.IntegerFieldFormat, "x", False, "1...2", "3...100", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.IntegerFieldFormat, "x", False, "3...4", "3...10000", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.IntegerFieldFormat, "x", False, "2...4", "-4000...100", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.IntegerFieldFormat, "x", False, "3...4", "-1000...100", _ANY_FORMAT)

    def test_fails_on_too_small_number(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...10", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "0")

    def test_fails_on_too_big_number(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...10", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "11")

    def test_fails_on_no_number(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...10", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "abc")

    def test_can_accept_valid_example(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1...10", _ANY_FORMAT)
        field_format.example = "3"
        self.assertEqual(field_format.example, "3")

    def test_fails_on_invalid_example(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _ANY_FORMAT)
        try:
            # NOTE: We cannot use dev_info.assert_raises_and_fnmatches() here
            # because the failing statement is an assignment, not a function
            # call.
            field_format.example = "11"
            self.fail()
        except errors.FieldValueError as anticipated_error:
            self.assertEqual('value is 11 but must be within range: 1...10', six.text_type(anticipated_error))


class RegExFieldFormatTest(unittest.TestCase):
    """
    Tests  for `RegExFieldFormat`.
    """
    def test_can_accept_matching_value(self):
        field_format = fields.RegExFieldFormat("x", False, None, r"a.*", _ANY_FORMAT)
        self.assertEqual(field_format.validated("abc"), "abc")

    def test_fails_on_unmatched_value(self):
        field_format = fields.RegExFieldFormat("x", False, None, r"a.*", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "xyz")

    def test_fails_on_broken_regex(self):
        try:
            fields.RegExFieldFormat("x", False, None, "*", _ANY_FORMAT)
            self.fail("broken pattern must raise error")
        except:
            # Ignore error caused by broken pattern. It would be better to use assertFails but
            # the interface to re.compile doesn't document a specific exception to be raised in
            # such a case.
            pass


class ChoiceFieldFormatTest(unittest.TestCase):
    """
    Tests  for `ChoiceFieldFormat`.
    """
    def test_can_match_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,grEEn,blue", _ANY_FORMAT)
        self.assertEqual(field_format.validated("red"), "red")
        self.assertEqual(field_format.validated("grEEn"), "grEEn")
        self.assertEqual(field_format.validated("blue"), "blue")

    def test_fails_on_empty_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,green,blue", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, '')

    def test_can_match_rule_embedded_in_blanks(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red, green ,blue ", _ANY_FORMAT)
        self.assertEqual(field_format.validated("green"), "green")

    def test_fails_on_wrong_case(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,grEEn,blue", _ANY_FORMAT)
        self.assertEqual(field_format.validated("grEEn"), "grEEn")
        self.assertRaises(errors.FieldValueError, field_format.validated, "green")
        self.assertRaises(errors.FieldValueError, field_format.validated, "blUE")

    def test_fails_on_improper_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,green,blue", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "tree")

    def test_can_match_only_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red", _ANY_FORMAT)
        self.assertEqual(field_format.validated("red"), "red")

    def test_can_match_non_ascii_choice(self):
        field_format = fields.ChoiceFieldFormat("geschlecht", False, None, "\"männlich\", \"weiblich\"", _ANY_FORMAT)
        self.assertEqual(field_format.validated("männlich"), "männlich")
        self.assertRaises(errors.FieldValueError, field_format.validated, "unbekannt")

    def test_can_match_possibly_empty_field_with_length(self):
        field_format = fields.ChoiceFieldFormat("optional_color", True, ":5", "red, green, blue", _ANY_FORMAT)
        self.assertEqual(field_format.validated("red"), "red")
        self.assertEqual(field_format.validated(""), "")

    def test_fails_on_empty_rule(self):
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, " ", _ANY_FORMAT)

    def test_fails_on_broken_rule(self):
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "red,", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, ",red", _ANY_FORMAT)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "red,,green", _ANY_FORMAT)


class ConstantFieldFormatTest(unittest.TestCase):
    """
    Tests  for `ConstantFieldFormat`.
    """
    def setUp(self):
        self._constant_format = fields.ConstantFieldFormat('constant', False, None, 'some', _ANY_FORMAT)

    def test_can_match_constant_name(self):
        self.assertEqual(self._constant_format.validated('some'), 'some')

    def test_can_match_constant_string(self):
        self._constant_format = fields.ConstantFieldFormat('constant', False, None, '"some"', _ANY_FORMAT)
        self.assertEqual(self._constant_format.validated('some'), 'some')

    def test_can_match_constant_integer(self):
        self._constant_format = fields.ConstantFieldFormat('constant', False, None, '3', _ANY_FORMAT)
        self.assertEqual(self._constant_format.validated('3'), '3')

    def test_can_match_constant_float(self):
        self._constant_format = fields.ConstantFieldFormat('constant', False, None, '3.1', _ANY_FORMAT)
        self.assertEqual(self._constant_format.validated('3.1'), '3.1')

    def test_fails_on_other_value(self):
        dev_test.assert_raises_and_fnmatches(
            self, errors.FieldValueError, "value is 'other' but must be constant: 'some'",
            self._constant_format.validated, 'other'
        )

    def test_fails_on_empty_value(self):
        self.assertRaises(errors.FieldValueError, self._constant_format.validated, '')

    def test_can_match_empty_constant(self):
        always_empty_format = fields.ConstantFieldFormat('constant', True, None, '', _ANY_FORMAT)
        self.assertEqual(always_empty_format.validated(''), '')

    def test_fails_on_empty_constant_with_non_empty_rule(self):
        dev_test.assert_raises_and_fnmatches(
            self, errors.InterfaceError,
            'to describe a Constant that can be empty, use a Choice field with a single choice',
            fields.ConstantFieldFormat, 'broken_empty', True, None, 'some', _ANY_FORMAT
        )

    def test_fails_on_missing_empty_flag_with_empty_rule(self):
        dev_test.assert_raises_and_fnmatches(
            self, errors.InterfaceError, 'field must be marked as empty to describe a constant empty value',
            fields.ConstantFieldFormat, 'broken_empty', False, None, '', _ANY_FORMAT)

    def test_fails_on_multiple_tokens_in_rule(self):
        dev_test.assert_raises_and_fnmatches(
            self, errors.InterfaceError, "constant rule must be a single Python token but also found: ';'",
            fields.ConstantFieldFormat, 'multiple_tokens', False, None, '"x";', _ANY_FORMAT)

    def test_fails_on_inconsistent_length(self):
        try:
            fields.ConstantFieldFormat('inconsistent_length', False, '2', '"a"', _ANY_FORMAT)
            self.fail()
        except errors.InterfaceError as anticipated_error:
            dev_test.assert_error_fnmatches(
                self, anticipated_error, "length is 2 but must be 1 to match constant 'a'")


class PatternFieldFormatTest(unittest.TestCase):
    """
    Tests for `PatternFieldFormat`.
    """
    def test_can_accept_value_matching_pattern(self):
        field_format = fields.PatternFieldFormat("x", False, None, "h*g?", _ANY_FORMAT)
        self.assertEqual(field_format.validated("hgo"), "hgo")
        self.assertEqual(field_format.validated("hugo"), "hugo")
        self.assertEqual(field_format.validated("huuuuga"), "huuuuga")

    def test_fails_on_value_not_matching_pattern(self):
        field_format = fields.PatternFieldFormat("x", False, None, "h*g?", _ANY_FORMAT)
        self.assertRaises(errors.FieldValueError, field_format.validated, "")
        self.assertRaises(errors.FieldValueError, field_format.validated, "hang")


class PublicFieldFunctionTest(unittest.TestCase):
    """
    Test for public functions in the fields module
    """
    def test_fails_on_non_ascii_character(self):
        self.assertRaises(errors.InterfaceError, fields.validated_field_name, "aä")


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
