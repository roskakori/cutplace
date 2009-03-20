"""Tests for checks module."""
import checks
import unittest

class IsUniqueCheckTest(unittest.TestCase):

    def testIsUniqueCheck(self):
        fieldNames = "branch_id customer_id first_name surname gender date_of_birth".split()
        check = checks.IsUniqueCheck("test check", "branch_id, customer_id", fieldNames)
        check.checkRow(1, [38000, 23, "John", "Doe", "male", "08.03.1957"])
        check.checkRow(2, [38000, 59, "Jane", "Miller", "female", "04.10.1946"])
        self.assertRaises(checks.CheckError, check.checkRow, 3, [38000, 59, "Jane", "Miller", "female", "04.10.1946"])

        # These methods should not do anything, but call them anyway for test sake.
        check.checkAtEnd()
        check.cleanup()

if __name__ == "__main__":
    unittest.main()