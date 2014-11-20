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
from cutplace import fields
from cutplace import errors

_anyFormat = data.DataFormat(data.FORMAT_DELIMITED)
_fixedFormat = data.DataFormat(data.FORMAT_FIXED)


def _createGermanDecimalFormat():
    germanFormat = data.DataFormat(data.FORMAT_DELIMITED)
    germanFormat.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
    germanFormat.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
    result = fields.DecimalFieldFormat("x", False, None, "", germanFormat)
    return result


class AbstractFieldFormatTest(unittest.TestCase):
    """
    Test for base validation in `AbstractFieldFormatTest`.
    """

    def testCanAcceptEmptyValueForFieldAllowedToBeEmpty(self):
        fieldFormat = fields.AbstractFieldFormat("x", True, None, "", _anyFormat)
        fieldFormat.validateEmpty("")

    def testCanRejectEmptyValueForFieldNotAllowedToBeEmpty(self):
        fieldFormat = fields.AbstractFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validateEmpty, "")

    def testValidateLength(self):
        fieldFormat = fields.AbstractFieldFormat("x", False, "3:5", "", _anyFormat)
        fieldFormat.validateLength("123")
        fieldFormat.validateLength("1234")
        fieldFormat.validateLength("12345")
        self.assertRaises(errors.FieldValueError, fieldFormat.validateLength, "12")
        self.assertRaises(errors.FieldValueError, fieldFormat.validateLength, "123456")

    def testEmptyAndLengthLimit(self):
        fieldFormat = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        fieldFormat.validateLength("")

    def testValidate(self):
        fieldFormat = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        self.assertRaises(NotImplementedError, fieldFormat.validated, "xyz")


class DateTimeFieldFormatTest(unittest.TestCase):
    """
    Tests  for `DateTimeFieldFormat`.
    """
    def testValidDates(self):
        fieldFormat = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        fieldFormat.validated("2000-01-01")
        fieldFormat.validated("2000-02-29")
        fieldFormat.validated("1955-02-28")
        fieldFormat.validated("2345-12-31")
        fieldFormat.validated("0001-01-01")
        fieldFormat.validated("9999-12-31")

    def testEmptyDate(self):
        fieldFormat = fields.DateTimeFieldFormat("x", True, None, "YYYY-MM-DD", _anyFormat)
        self.assertEquals(fieldFormat.validated(""), None)
        self.assertNotEquals(fieldFormat.validated("2000-01-01"), None)

    def testBrokenDates(self):
        fieldFormat = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "2000-02-30")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "0000-01-01")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "this is a bad day")

        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        fieldFormat.validated("2000-1-1")

    def testPercentSign(self):
        fieldFormat = fields.DateTimeFieldFormat("x", False, None, "%YYYY-MM-DD", _anyFormat)
        fieldFormat.validated("%2000-01-01")


class DecimalFieldFormatTest(unittest.TestCase):
    """
    Test for `DecimalFieldFormat`.
    """
    def testValidDecimals(self):
        fieldFormat = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertEqual(decimal.Decimal("17.23"), fieldFormat.validated("17.23"))
        self.assertEqual(decimal.Decimal("17.123456789"), fieldFormat.validated("17.123456789"))

    def testValidGermanDecimals(self):
        germanDataFormat = data.DataFormat(data.FORMAT_DELIMITED)
        germanDataFormat.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
        germanDataFormat.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
        germanDecimalFieldformat = _createGermanDecimalFormat()
        self.assertEqual(decimal.Decimal("17.23"), germanDecimalFieldformat.validated("17,23"))
        self.assertEqual(decimal.Decimal("12345678"), germanDecimalFieldformat.validated("12.345.678"))
        self.assertEqual(decimal.Decimal("171234567.89"), germanDecimalFieldformat.validated("171.234.567,89"))

    def testBrokenDecimals(self):
        fieldFormat = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "eggs")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "12.345,678")

        germanFormat = _createGermanDecimalFormat()
        self.assertRaises(errors.FieldValueError, germanFormat.validated, "12,345,678")
        self.assertRaises(errors.FieldValueError, germanFormat.validated, "12,345.678")

    def testBrokenDecimalSyntax(self):
        self.assertRaises(errors.FieldSyntaxError, fields.DecimalFieldFormat, "x", False, None, "eggs", _anyFormat)


class IntegerFieldFormatTest(unittest.TestCase):
    """
    Tests  for `IntegerFieldFormat`.
    """
    def testWithinRange(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertEquals(fieldFormat.validated("1"), 1)
        self.assertEquals(fieldFormat.validated("7"), 7)
        self.assertEquals(fieldFormat.validated("10"), 10)
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "123", _anyFormat)
        self.assertEquals(fieldFormat.validated("123"), 123)

    def testTooSmall(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "0")

    def testTooBig(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "11")

    def testNoNumber(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "abc")

    def testAsIcdRow(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        length = fieldFormat.length
        items = length.items
        self.assertEquals(items, None)
        self.assertEquals(fieldFormat.asIcdRow(), ["x", "", "", "", "Integer", "1:10"])

    def testCanProcessValidExample(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        fieldFormat.example = "3"
        self.assertEqual(fieldFormat.example, "3")

    def testFailsOnInvalidExample(self):
        fieldFormat = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        try:
            fieldFormat.example = "11"
        except errors.FieldValueError:
            # Ignore expected error.
            pass


class RegExFieldFormatTest(unittest.TestCase):
    """
    Tests  for `RegExFieldFormat`.
    """
    def testMatch(self):
        fieldFormat = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertEquals(fieldFormat.validated("abc"), "abc")

    def testNoMatch(self):
        fieldFormat = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "xyz")

    def testBrokenRegEx(self):
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
    def testMatchingChoice(self):
        fieldFormat = fields.ChoiceFieldFormat("color", False, None, "red,grEEn, blue ", _anyFormat)
        self.assertEquals(fieldFormat.validated("red"), "red")
        # Value without blanks around it.
        self.assertEquals(fieldFormat.validated("grEEn"), "grEEn")
        # Value with blanks around it.
        self.assertEquals(fieldFormat.validated("blue"), "blue")
        # Disregard upper/lower case.
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "gReen")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "")

    def testImproperChoice(self):
        fieldFormat = fields.ChoiceFieldFormat("color", False, None, "red,green, blue ", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "tree")

    def testMatchingOnlyChoice(self):
        fieldFormat = fields.ChoiceFieldFormat("color", False, None, "red", _anyFormat)
        self.assertEquals(fieldFormat.validated("red"), "red")

    def testMatchWithUmlaut(self):
        fieldFormat = fields.ChoiceFieldFormat("geschlecht", False, None, "\"männlich\", \"weiblich\"", _anyFormat)
        self.assertEquals(fieldFormat.validated("männlich"), "männlich")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "unbekannt")

    def testPossiblyEmptyFieldWithLength(self):
        fieldFormat = fields.ChoiceFieldFormat("optional_color", True, ":5", "red, green, blue", _anyFormat)
        self.assertEquals(fieldFormat.validated("red"), "red")
        self.assertEquals(fieldFormat.validated(""), "")

    def testBrokenEmptyChoice(self):
        self.assertRaises(errors.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "", _anyFormat)
        self.assertRaises(errors.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, " ", _anyFormat)
        self.assertRaises(errors.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "red,", _anyFormat)
        self.assertRaises(errors.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, ",red", _anyFormat)
        self.assertRaises(errors.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "red,,green", _anyFormat)


class PatternFieldFormatTest(unittest.TestCase):
    """
    Tests for `PatternFieldFormat`.
    """
    def testCanAcceptValueMatchingPattern(self):
        fieldFormat = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertEquals(fieldFormat.validated("hgo"), "hgo")
        self.assertEquals(fieldFormat.validated("hugo"), "hugo")
        self.assertEquals(fieldFormat.validated("huuuuga"), "huuuuga")

    def testFailsOnValueNotMatchingPattern(self):
        fieldFormat = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "")
        self.assertRaises(errors.FieldValueError, fieldFormat.validated, "hang")

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
