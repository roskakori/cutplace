"""Tests  for field formats."""
import fields
import logging#
import unittest

class DateTimeFieldFormatTest(unittest.TestCase):
    """Tests  for DateTimeFieldFormat."""
    def testValidDates(self):
        format = fields.DateFieldFormat("x", "YYYY-MM-DD", False)
        format.validate("2000-01-01")
        format.validate("2000-02-29")
        format.validate("1955-02-28")
        format.validate("2345-12-31")
        format.validate("0001-01-01")
        format.validate("9999-12-31")

    def testBrokenDates(self):
        format = fields.DateFieldFormat("x", "YYYY-MM-DD", False)
        self.assertRaises(fields.FieldValueError, format.validate, "2000-02-30")
        self.assertRaises(fields.FieldValueError, format.validate, "0000-01-01")
        self.assertRaises(fields.FieldValueError, format.validate, "this is a bad day")
        
        # FIXME: Raise FieldValueError for the following value due lack of leading zeros.
        format.validate("2000-1-1")

class IntegerFieldFormatTest(unittest.TestCase):
    """Tests  for IntegerFieldFormat."""
    def testWithinRange(self):
        format = fields.IntegerFieldFormat("x", "1...10", False)
        format.validate("1")
        format.validate("7")
        format.validate("10")
        format = fields.IntegerFieldFormat("x", "123", False)
        format.validate("123")

    def testTooSmall(self):
        format = fields.IntegerFieldFormat("x", "1...10", False)
        self.assertRaises(fields.FieldValueError, format.validate, "0")

    def testTooBig(self):
        format = fields.IntegerFieldFormat("x", "1...10", False)
        self.assertRaises(fields.FieldValueError, format.validate, "11")
        
    def testNoNumber(self):
        format = fields.IntegerFieldFormat("x", "1...10", False)
        self.assertRaises(fields.FieldValueError, format.validate, "abc")
        
class RegExFieldFormatTest(unittest.TestCase):
    """Tests  for RegExFieldFormat."""
    def testMatch(self):
        format = fields.RegExFieldFormat("x", r"a.*", False)
        format.validate("abc")

    def testNoMatch(self):
        format = fields.RegExFieldFormat("x", r"a.*", False)
        self.assertRaises(fields.FieldValueError, format.validate, "xyz")
    
    def testBrokenRegEx(self):
        try:
            format = fields.RegExFieldFormat("x", "*", False)
            self.fail("broken pattern must raise error")
        except:
            # Ignore error caused by broken pattern. It would be better to use assertFails but
            # the interface to re.compile doesn't document a specific exception to be raised in
            # such a case.
            pass

class ChoiceFieldFormatTest(unittest.TestCase):
    """Tests  for ChoiceFieldFormat."""
    def testMatchingChoice(self):
        format = fields.ChoiceFieldFormat("color", "red,grEEn, blue ", False)
        format.validate("red")
        # Value without blanks around it.
        format.validate("grEEn")
        # Value with blanks around it.
        format.validate("blue")
        # Disregard upper/lower case.
        format.validate("gReen")
        
    def testImproperChoice(self):
        format = fields.ChoiceFieldFormat("color", "red,green, blue ", False)
        self.assertRaises(fields.FieldValueError, format.validate, "tree")
        
    def testMatchingOnlyChoice(self):
        format = fields.ChoiceFieldFormat("color", "red", False)
        format.validate("red")

    def testEmptyChoice(self):
        # FIXME: Should cause ValueError
        format = fields.ChoiceFieldFormat("color", " ", False)
        format = fields.ChoiceFieldFormat("color", "red, ", False)

class PatternFieldTest(unittest.TestCase):
    """Tests for PatternFieldFormat."""
    def testMatch(self):
        format = fields.PatternField("x", "h*g?", False)
        format.validate("hgo")
        format.validate("hugo")
        format.validate("huuuuga")
    
    def testNoMatch(self):
        format = fields.PatternField("x", "h*g?", False)
        self.assertRaises(fields.FieldValueError, format.validate, "")
        self.assertRaises(fields.FieldValueError, format.validate, "hang")

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
