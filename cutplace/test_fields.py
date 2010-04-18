# -*- coding: iso-8859-15 -*-
"""
Tests  for field formats.
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
import data
import decimal
import fields
import logging
import unittest

_anyFormat = data.createDataFormat(data.FORMAT_CSV)
_fixedFormat = data.createDataFormat(data.FORMAT_FIXED)

def _createGermanDecimalFormat():
    germanFormat = data.createDataFormat(data.FORMAT_CSV)
    germanFormat.set(data.KEY_DECIMAL_SEPARATOR, ",")
    germanFormat.set(data.KEY_THOUSANDS_SEPARATOR, ".")
    result = fields.DecimalFieldFormat("x", False, None, "", germanFormat)
    return result

class AbstractFieldFormatTest(unittest.TestCase):
    """
    Test for base validation in `AbstractFieldFormatTest`.
    """

    def testValidateEmpty(self):
        format = fields.AbstractFieldFormat("x", True, None, "", _anyFormat)
        format.validateEmpty("")
        format = fields.AbstractFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validateEmpty, "")

    def testValidateLength(self):
        format = fields.AbstractFieldFormat("x", False, "3:5", "", _anyFormat)
        format.validateLength("123")
        format.validateLength("1234")
        format.validateLength("12345")
        self.assertRaises(fields.FieldValueError, format.validateLength, "12")
        self.assertRaises(fields.FieldValueError, format.validateLength, "123456")

    def testEmptyAndLengthLimit(self):
        format = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        format.validateLength("")
        
    def testValidate(self):
        format = fields.AbstractFieldFormat("x", True, "3:5", "", _anyFormat)
        self.assertRaises(NotImplementedError, format.validated, "xyz")
        
class DateTimeFieldFormatTest(unittest.TestCase):
    """
    Tests  for `DateTimeFieldFormat`.
    """
    def testValidDates(self):
        format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        format.validated("2000-01-01")
        format.validated("2000-02-29")
        format.validated("1955-02-28")
        format.validated("2345-12-31")
        format.validated("0001-01-01")
        format.validated("9999-12-31")

    def testEmptyDate(self):
        format = fields.DateTimeFieldFormat("x", True, None, "YYYY-MM-DD", _anyFormat)
        self.assertEquals(format.validated(""), None)
        self.assertNotEquals(format.validated("2000-01-01"), None)

    def testBrokenDates(self):
        format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "2000-02-30")
        self.assertRaises(fields.FieldValueError, format.validated, "0000-01-01")
        self.assertRaises(fields.FieldValueError, format.validated, "this is a bad day")
        
        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        format.validated("2000-1-1")

    def testPercentSign(self):
        format = fields.DateTimeFieldFormat("x", False, None, "%YYYY-MM-DD", _anyFormat)
        format.validated("%2000-01-01")

class DecimalFieldFormatTest(unittest.TestCase):
    """
    Test for `DecimalFieldFormat`.
    """
    def testValidDecimals(self):
        format = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertEqual(decimal.Decimal("17.23"), format.validated("17.23"))
        self.assertEqual(decimal.Decimal("17.123456789"), format.validated("17.123456789"))

    def testValidGermanDecimals(self):
        germanFormat = data.createDataFormat(data.FORMAT_CSV)
        germanFormat.set(data.KEY_DECIMAL_SEPARATOR, ",")
        germanFormat.set(data.KEY_THOUSANDS_SEPARATOR, ".")
        format =_createGermanDecimalFormat()
        self.assertEqual(decimal.Decimal("17.23"), format.validated("17,23"))
        self.assertEqual(decimal.Decimal("171234567.89"), format.validated("171.234.567,89"))

    def testBrokenDecimals(self):
        format = fields.DecimalFieldFormat("x", False, None, "", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "")
        self.assertRaises(fields.FieldValueError, format.validated, "eggs")
        self.assertRaises(fields.FieldValueError, format.validated, "12.345,678")

        germanFormat = _createGermanDecimalFormat()
        self.assertRaises(fields.FieldValueError, format.validated, "12.345,678")
        self.assertRaises(fields.FieldValueError, format.validated, "12.345.678")
        
    def testBrokenDecimalSyntax(self):
        self.assertRaises(fields.FieldSyntaxError, fields.DecimalFieldFormat, "x", False, None, "eggs", _anyFormat)
        
class IntegerFieldFormatTest(unittest.TestCase):
    """
    Tests  for `IntegerFieldFormat`.
    """
    def testWithinRange(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertEquals(format.validated("1"), 1)
        self.assertEquals(format.validated("7"), 7)
        self.assertEquals(format.validated("10"), 10)
        format = fields.IntegerFieldFormat("x", False, None, "123", _anyFormat)
        self.assertEquals(format.validated("123"), 123)

    def testTooSmall(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "0")

    def testTooBig(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "11")
        
    def testNoNumber(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "abc")
        
class RegExFieldFormatTest(unittest.TestCase):
    """
    Tests  for `RegExFieldFormat`.
    """
    def testMatch(self):
        format = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertEquals(format.validated("abc"), "abc")

    def testNoMatch(self):
        format = fields.RegExFieldFormat("x", False, None, r"a.*", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "xyz")
    
    def testBrokenRegEx(self):
        try:
            format = fields.RegExFieldFormat("x", False, None, "*", _anyFormat)
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
        format = fields.ChoiceFieldFormat("color", False, None, "red,grEEn, blue ", _anyFormat)
        self.assertEquals(format.validated("red"), "red")
        # Value without blanks around it.
        self.assertEquals(format.validated("grEEn"), "grEEn")
        # Value with blanks around it.
        self.assertEquals(format.validated("blue"), "blue")
        # Disregard upper/lower case.
        self.assertRaises(fields.FieldValueError, format.validated, "gReen")
        self.assertRaises(fields.FieldValueError, format.validated, "")
        
    def testImproperChoice(self):
        format = fields.ChoiceFieldFormat("color", False, None, "red,green, blue ", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "tree")
        
    def testMatchingOnlyChoice(self):
        format = fields.ChoiceFieldFormat("color", False, None, "red", _anyFormat)
        self.assertEquals(format.validated("red"), "red")

    def testMatchWithUmlaut(self):
        format = fields.ChoiceFieldFormat("geschlecht", False, None, u"\"männlich\", \"weiblich\"", _anyFormat)
        self.assertEquals(format.validated(u"männlich"), u"männlich")
        self.assertRaises(fields.FieldValueError, format.validated, u"unbekannt")

    def testPossiblyEmptyFieldWithLength(self):
        format = fields.ChoiceFieldFormat("optional_color", True, ":5", "red, green, blue", _anyFormat)
        self.assertEquals(format.validated("red"), "red")
        self.assertEquals(format.validated(""), "")
        
    def testBrokenEmptyChoice(self):
        self.assertRaises(fields.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "", _anyFormat)
        self.assertRaises(fields.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, " ", _anyFormat)
        self.assertRaises(fields.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "red,", _anyFormat)
        self.assertRaises(fields.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, ",red", _anyFormat)
        self.assertRaises(fields.FieldSyntaxError, fields.ChoiceFieldFormat, "color", False, None, "red,,green", _anyFormat)

class PatternFieldFormatTest(unittest.TestCase):
    """
    Tests for `PatternFieldFormat`.
    """
    def testMatch(self):
        format = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertEquals(format.validated("hgo"), "hgo") 
        self.assertEquals(format.validated("hugo"), "hugo")
        self.assertEquals(format.validated("huuuuga"), "huuuuga")
    
    def testNoMatch(self):
        format = fields.PatternFieldFormat("x", False, None, "h*g?", _anyFormat)
        self.assertRaises(fields.FieldValueError, format.validated, "")
        self.assertRaises(fields.FieldValueError, format.validated, "hang")

if __name__ == '__main__': # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
