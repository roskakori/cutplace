# -*- coding: iso-8859-15 -*-
"""
Tests  for field formats.
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
import decimal
import logging
import unittest

from cutplace import data
from cutplace import errors
from cutplace import fields

_anyFormat = data.DataFormat(data.FORMAT_DELIMITED)
_fixedFormat = data.DataFormat(data.FORMAT_FIXED)


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
        field_format = fields.AbstractFieldFormat("x", True, None, "", _anyFormat)
        field_format.validate_empty("")

    def test_can_reject_empty_value_for_field_not_allowed_to_be_empty(self):
        field_format = fields.AbstractFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validate_empty, "")

    def test_validate_length(self):
        field_format = fields.AbstractFieldFormat("x", False, "3:5", "", _anyFormat)
        field_format.validate_length("123")
        field_format.validate_length("1234")
        field_format.validate_length("12345")
        self.assertRaises(errors.FieldValueError, field_format.validate_length, "12")
        self.assertRaises(errors.FieldValueError, field_format.validate_length, "123456")

    def test_empty_and_length_limit(self):
        field_format = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        field_format.validate_length("")

    def test_validate(self):
        field_format = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        self.assertRaises(NotImplementedError, field_format.validated, "xyz")


class DateTimeFieldFormatTest(unittest.TestCase):
    """
    Tests  for `DateTimeFieldFormat`.
    """
    def test_valid_dates(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        field_format.validated("2000-01-01")
        field_format.validated("2000-02-29")
        field_format.validated("1955-02-28")
        field_format.validated("2345-12-31")
        field_format.validated("0001-01-01")
        field_format.validated("9999-12-31")

    def test_empty_date(self):
        field_format = fields.DateTimeFieldFormat("x", True, None, "YYYY-MM-DD", _anyFormat)
        self.assertEquals(field_format.validated(""), None)
        self.assertNotEquals(field_format.validated("2000-01-01"), None)

    def test_broken_dates(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "2000-02-30")
        self.assertRaises(errors.FieldValueError, field_format.validated, "0000-01-01")
        self.assertRaises(errors.FieldValueError, field_format.validated, "this is a bad day")

        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        field_format.validated("2000-1-1")

    def test_percent_sign(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "%YYYY-MM-DD", _anyFormat)
        field_format.validated("%2000-01-01")


class DecimalFieldFormatTest(unittest.TestCase):
    """
    Test for `DecimalFieldFormat`.
    """
    def test_valid_decimals(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertEqual(decimal.Decimal("17.23"), field_format.validated("17.23"))
        self.assertEqual(decimal.Decimal("17.123456789"), field_format.validated("17.123456789"))

    def test_valid_german_decimals(self):
        german_data_format = data.DataFormat(data.FORMAT_DELIMITED)
        german_data_format.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
        german_data_format.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
        german_decimal_field_format = _create_german_decimal_format()
        self.assertEqual(decimal.Decimal("17.23"), german_decimal_field_format.validated("17,23"))
        self.assertEqual(decimal.Decimal("12345678"), german_decimal_field_format.validated("12.345.678"))
        self.assertEqual(decimal.Decimal("171234567.89"), german_decimal_field_format.validated("171.234.567,89"))

    def test_broken_decimals(self):
        field_format = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "")
        self.assertRaises(errors.FieldValueError, field_format.validated, "eggs")
        self.assertRaises(errors.FieldValueError, field_format.validated, "12.345,678")

        german_format = _create_german_decimal_format()
        self.assertRaises(errors.FieldValueError, german_format.validated, "12,345,678")
        self.assertRaises(errors.FieldValueError, german_format.validated, "12,345.678")

    def test_broken_decimal_syntax(self):
        self.assertRaises(errors.InterfaceError, fields.DecimalFieldFormat, "x", False, None, "eggs", _anyFormat)


class IntegerFieldFormatTest(unittest.TestCase):
    """
    Tests  for `IntegerFieldFormat`.
    """
    def test_within_range(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertEquals(field_format.validated("1"), 1)
        self.assertEquals(field_format.validated("7"), 7)
        self.assertEquals(field_format.validated("10"), 10)
        field_format = fields.IntegerFieldFormat("x", False, None, "123", _anyFormat)
        self.assertEquals(field_format.validated("123"), 123)

    def test_too_small(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "0")

    def test_too_big(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "11")

    def test_no_number(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "abc")

    def test_as_icd_row(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        length = field_format.length
        items = length.items
        self.assertEquals(items, None)
        self.assertEquals(field_format.as_icd_row(), ["x", "", "", "", "Integer", "1:10"])

    def test_can_process_valid_example(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        field_format.example = "3"
        self.assertEqual(field_format.example, "3")

    def test_fails_on_invalid_example(self):
        field_format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        try:
            field_format.example = "11"
        except errors.FieldValueError:
            # Ignore expected error.
            pass


class RegExFieldFormatTest(unittest.TestCase):
    """
    Tests  for `RegExFieldFormat`.
    """
    def test_match(self):
        field_format = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertEquals(field_format.validated("abc"), "abc")

    def test_no_match(self):
        field_format = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "xyz")

    def test_broken_regex(self):
        try:
            fields.RegExFieldFormat("x", False, None, "*", _anyFormat)
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
    def test_matching_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,grEEn, blue ", _anyFormat)
        self.assertEquals(field_format.validated("red"), "red")
        # Value without blanks around it.
        self.assertEquals(field_format.validated("grEEn"), "grEEn")
        # Value with blanks around it.
        self.assertEquals(field_format.validated("blue"), "blue")
        # Disregard upper/lower case.
        self.assertRaises(errors.FieldValueError, field_format.validated, "gReen")
        self.assertRaises(errors.FieldValueError, field_format.validated, "")

    def test_improper_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red,green, blue ", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "tree")

    def test_matching_only_choice(self):
        field_format = fields.ChoiceFieldFormat("color", False, None, "red", _anyFormat)
        self.assertEquals(field_format.validated("red"), "red")

    def test_match_with_umlaut(self):
        field_format = fields.ChoiceFieldFormat("geschlecht", False, None, "\"männlich\", \"weiblich\"", _anyFormat)
        self.assertEquals(field_format.validated("männlich"), "männlich")
        self.assertRaises(errors.FieldValueError, field_format.validated, "unbekannt")

    def test_possibly_empty_field_with_length(self):
        field_format = fields.ChoiceFieldFormat("optional_color", True, ":5", "red, green, blue", _anyFormat)
        self.assertEquals(field_format.validated("red"), "red")
        self.assertEquals(field_format.validated(""), "")

    def test_broken_empty_choice(self):
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "", _anyFormat)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, " ", _anyFormat)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "red,", _anyFormat)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, ",red", _anyFormat)
        self.assertRaises(errors.InterfaceError, fields.ChoiceFieldFormat, "color", False, None, "red,,green", _anyFormat)


class PatternFieldFormatTest(unittest.TestCase):
    """
    Tests for `PatternFieldFormat`.
    """
    def test_can_accept_value_matching_pattern(self):
        field_format = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertEquals(field_format.validated("hgo"), "hgo")
        self.assertEquals(field_format.validated("hugo"), "hugo")
        self.assertEquals(field_format.validated("huuuuga"), "huuuuga")

    def test_fails_on_value_not_matching_pattern(self):
        field_format = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertRaises(errors.FieldValueError, field_format.validated, "")
        self.assertRaises(errors.FieldValueError, field_format.validated, "hang")

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
