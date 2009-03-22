"""Tests for checks module."""
import checks
import fields
import unittest

def _createFieldMap(fieldNames, fieldValues):
    assert fieldNames
    assert fieldValues
    assert len(fieldNames) == len(fieldValues)
    
    # FIXME: There must be a more pythonic way to do this.
    result = {}
    for fieldIndex in range(0, len(fieldNames) - 1):
        result[fieldNames[fieldIndex]] = fieldValues[fieldIndex]
    return result

def _getTestFieldNames():
    return "branch_id customer_id first_name surname gender date_of_birth".split()

class IsUniqueCheckTest(unittest.TestCase):
    def testIsUniqueCheck(self):
        fieldNames = _getTestFieldNames()
        check = checks.IsUniqueCheck("test check", "branch_id, customer_id", fieldNames)
        check.checkRow(1, _createFieldMap(fieldNames, [38000, 23, "John", "Doe", "male", "08.03.1957"]))
        check.checkRow(2, _createFieldMap(fieldNames, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]))
        self.assertRaises(checks.CheckError, check.checkRow, 3,
                          _createFieldMap(fieldNames, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]))

        # These methods should not do anything, but call them anyway for test sake.
        check.checkAtEnd()
        check.cleanup()

class DistinctCountCheckTest(unittest.TestCase):
    def testDistinctCountCheck(self):
        fieldNames = _getTestFieldNames()
        check = checks.DistinctCountCheck("test check", "branch_id<3", fieldNames)
        check = checks.DistinctCountCheck("test check", "branch_id < 3", fieldNames)
        check.checkRow(1, _createFieldMap(fieldNames, [38000, 23, "John", "Doe", "male", "08.03.1957"]))
        check.checkRow(2, _createFieldMap(fieldNames, [38001, 59, "Jane", "Miller", "female", "04.10.1946"]))
        check.checkAtEnd()
        check.checkRow(2, _createFieldMap(fieldNames, [38003, 59, "Jane", "Miller", "female", "04.10.1946"]))
        self.assertRaises(checks.CheckError, check.checkAtEnd)

    def testBrokenExpressions(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(checks.CheckSyntaxError, checks.DistinctCountCheck, "broken", "", fieldNames)
        self.assertRaises(checks.CheckSyntaxError, checks.DistinctCountCheck, "broken", " ", fieldNames)
        self.assertRaises(fields.FieldLookupError, checks.DistinctCountCheck, "broken", "hugo < 3", fieldNames)
        self.assertRaises(checks.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id < (100 / 0)", fieldNames)
        self.assertRaises(checks.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id ! broken ^ 5ynt4x ?!?", fieldNames)
        self.assertRaises(checks.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id + 123", fieldNames)

if __name__ == "__main__":
    unittest.main()