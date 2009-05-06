"""
Tests  for field formats.
"""
import fields
import logging
import unittest

class AbstractFieldFormatTest(unittest.TestCase):
    """
    Test for base validation in `AbstractFieldFormatTest`. This does not include `validate()`, which always raises a
    `NotImplementedError`.
    """
    def testValidateEmpty(self):
        format = fields.AbstractFieldFormat("x", True, None, "")
        format.validateEmpty("")
        format = fields.AbstractFieldFormat("x", False, None, "")
        self.assertRaises(fields.FieldValueError, format.validateEmpty, "")

    def testValidateLength(self):
        format = fields.AbstractFieldFormat("x", False, "3:5", "")
        format.validateLength("123")
        format.validateLength("1234")
        format.validateLength("12345")
        self.assertRaises(fields.FieldValueError, format.validateLength, "12")
        self.assertRaises(fields.FieldValueError, format.validateLength, "123456")

    def testEmptyAndLengthLimit(self):
        format = fields.AbstractFieldFormat("x", True, "3:5", "")
        format.validateLength("")
        
class DateTimeFieldFormatTest(unittest.TestCase):
    """
    Tests  for `DateTimeFieldFormat`.
    """
    def testValidDates(self):
        format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD")
        format.validate("2000-01-01")
        format.validate("2000-02-29")
        format.validate("1955-02-28")
        format.validate("2345-12-31")
        format.validate("0001-01-01")
        format.validate("9999-12-31")

    def testBrokenDates(self):
        format = fields.DateTimeFieldFormat("x", False, None, "YYYY-MM-DD")
        self.assertRaises(fields.FieldValueError, format.validate, "2000-02-30")
        self.assertRaises(fields.FieldValueError, format.validate, "0000-01-01")
        self.assertRaises(fields.FieldValueError, format.validate, "this is a bad day")
        
        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        format.validate("2000-1-1")

    def testPercentSign(self):
        format = fields.DateTimeFieldFormat("x", False, None, "%YYYY-MM-DD")
        format.validate("%2000-01-01")


class IntegerFieldFormatTest(unittest.TestCase):
    """
    Tests  for `IntegerFieldFormat`.
    """
    def testWithinRange(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10")
        format.validate("1")
        format.validate("7")
        format.validate("10")
        format = fields.IntegerFieldFormat("x", False, None, "123")
        format.validate("123")

    def testTooSmall(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10")
        self.assertRaises(fields.FieldValueError, format.validate, "0")

    def testTooBig(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10")
        self.assertRaises(fields.FieldValueError, format.validate, "11")
        
    def testNoNumber(self):
        format = fields.IntegerFieldFormat("x", False, None, "1:10")
        self.assertRaises(fields.FieldValueError, format.validate, "abc")
        
class RegExFieldFormatTest(unittest.TestCase):
    """
    Tests  for `RegExFieldFormat`.
    """
    def testMatch(self):
        format = fields.RegExFieldFormat("x", False, None, r"a.*")
        format.validate("abc")

    def testNoMatch(self):
        format = fields.RegExFieldFormat("x", False, None, r"a.*")
        self.assertRaises(fields.FieldValueError, format.validate, "xyz")
    
    def testBrokenRegEx(self):
        try:
            format = fields.RegExFieldFormat("x", False, None, "*")
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
        format = fields.ChoiceFieldFormat("color", False, None, "red,grEEn, blue ")
        format.validate("red")
        # Value without blanks around it.
        format.validate("grEEn")
        # Value with blanks around it.
        format.validate("blue")
        # Disregard upper/lower case.
        format.validate("gReen")
        
    def testImproperChoice(self):
        format = fields.ChoiceFieldFormat("color", False, None, "red,green, blue ")
        self.assertRaises(fields.FieldValueError, format.validate, "tree")
        
    def testMatchingOnlyChoice(self):
        format = fields.ChoiceFieldFormat("color", False, None, "red")
        format.validate("red")

    def testEmptyChoice(self):
        # FIXME: Should cause ValueError
        format = fields.ChoiceFieldFormat("color", False, None, " ")
        format = fields.ChoiceFieldFormat("color", False, None, "red, ")

class PatternFieldFormatTest(unittest.TestCase):
    """
    Tests for `PatternFieldFormat`.
    """
    def testMatch(self):
        format = fields.PatternFieldFormat("x", False, None, "h*g?")
        format.validate("hgo")
        format.validate("hugo")
        format.validate("huuuuga")
    
    def testNoMatch(self):
        format = fields.PatternFieldFormat("x", False, None, "h*g?")
        self.assertRaises(fields.FieldValueError, format.validate, "")
        self.assertRaises(fields.FieldValueError, format.validate, "hang")

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
