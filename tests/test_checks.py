"""
Tests for `checks` module.
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
import logging
import unittest

from cutplace import checks
from cutplace import errors
from cutplace import fields


def _createFieldMap(fieldNames, fieldValues):
    assert fieldNames
    assert fieldValues
    assert len(fieldNames) == len(fieldValues)

    # FIXME: There must be a more pythonic way to do this.
    result = {}
    for fieldIndex in range(len(fieldNames) - 1):
        result[fieldNames[fieldIndex]] = fieldValues[fieldIndex]
    return result


def _getTestFieldNames():
    return "branch_id customer_id first_name surname gender date_of_birth".split()


class _AbstractCheckTest(unittest.TestCase):
    def testStr(self):
        fieldNames = _getTestFieldNames()
        # TODO: Create an instance of the current class instead of _AbstractCheck even for ancestors.
        check = checks.AbstractCheck("test check", "", fieldNames)
        self.assertTrue(check.__str__())

    def testLocation(self):
        fieldNames = _getTestFieldNames()
        check = checks.AbstractCheck("test check", "", fieldNames)
        self.assertTrue(check.location is not None)

    def testMissingFieldNames(self):
        self.assertRaises(errors.FieldLookupError, checks.AbstractCheck, "missing fields", "", [])

    def testCheckRow(self):
        # HACK: This is just here to make coverage happy because "# pragma: no cover" does not work
        # on methods that consist of nothing but a single "pass".
        fieldNames = _getTestFieldNames()
        check = checks.AbstractCheck("test check", "", fieldNames)
        location = errors.InputLocation(self.testCheckRow, has_cell=True)
        check.check_row([], location)


class IsUniqueCheckTest(_AbstractCheckTest):
    def testIsUniqueCheck(self):
        fieldNames = _getTestFieldNames()
        check = checks.IsUniqueCheck("test check", "branch_id, customer_id", fieldNames)
        location = errors.InputLocation(self.testIsUniqueCheck, has_cell=True)
        check.check_row(_createFieldMap(fieldNames, [38000, 23, "John", "Doe", "male", "08.03.1957"]), location)
        location.advance_line()
        check.check_row(_createFieldMap(fieldNames, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        location.advance_line()
        try:
            check.check_row(_createFieldMap(fieldNames, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]),
                            location)
            self.fail("duplicate row must cause CheckError")
        except errors.CheckError as error:
            self.assertTrue(error.see_also_location)
            self.assertNotEqual(location, error.see_also_location)
            self.assertEqual(error.location.cell, 0)

        # These methods should not do anything, but call them anyway for test sake.
        check.check_at_end(location)
        check.cleanup()

    def testBrokenUniqueCheckWithMissingFields(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "", fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "   ", fieldNames)

    def testBrokenUniqueCheckWithTwoSequentialCommas(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "branch_id,,customer_id", fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "branch_id,,", fieldNames)

    def testBrokenUniqueCheckWithCommaAtStart(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", ",branch_id", fieldNames)

    def testBrokenUniqueCheckWithBrokenFieldName(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "branch_id, customer-id", fieldNames)

    def testBrokenUniqueCheckWithMissingComma(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", "branch_id customer_id", fieldNames)

    def testFailsOnDuplicateFieldName(self):
        fieldNames = _getTestFieldNames()
        firstFieldName = fieldNames[0]
        brokenUniqueFieldNames = ", ".join([firstFieldName, firstFieldName])
        self.assertRaises(errors.CheckSyntaxError, checks.IsUniqueCheck, "test check", brokenUniqueFieldNames, fieldNames)


class DistinctCountCheckTest(unittest.TestCase):
    def testDistinctCountCheck(self):
        fieldNames = _getTestFieldNames()
        checks.DistinctCountCheck("test check", "branch_id<3", fieldNames)
        check = checks.DistinctCountCheck("test check", "branch_id < 3", fieldNames)
        location = errors.InputLocation(self.testDistinctCountCheck, has_cell=True)
        check.check_row(_createFieldMap(fieldNames, [38000, 23, "John", "Doe", "male", "08.03.1957"]), location)
        location.advance_line()
        check.check_row(_createFieldMap(fieldNames, [38001, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        check.check_at_end(location)
        location.advance_line()
        check.check_row(_createFieldMap(fieldNames, [38003, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        self.assertRaises(errors.CheckError, check.check_at_end, location)

    def testBrokenExpressions(self):
        fieldNames = _getTestFieldNames()
        self.assertRaises(errors.CheckSyntaxError, checks.DistinctCountCheck, "broken", "", fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.DistinctCountCheck, "broken", " ", fieldNames)
        self.assertRaises(errors.FieldLookupError, checks.DistinctCountCheck, "broken", "hugo < 3", fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id < (100 / 0)", fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id ! broken ^ 5ynt4x ?!?",
                          fieldNames)
        self.assertRaises(errors.CheckSyntaxError, checks.DistinctCountCheck, "broken", "branch_id + 123", fieldNames)

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
