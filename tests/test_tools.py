"""
Test for `tools` module.
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
import os.path
import unittest

from cutplace import dev_test
from cutplace import _tools


class ToolsTest(unittest.TestCase):
    """TestCase for tools module."""
    def testCanCreateTestDateTime(self):
        for _ in range(15):
            dateTime = dev_test.createTestDateTime()
            self.assertTrue(dateTime is not None)
            self.assertNotEqual(dateTime, "")

    def testCanCreateTestName(self):
        for _ in range(15):
            name = dev_test.createTestName()
            self.assertTrue(name is not None)
            self.assertNotEqual(name, "")

    def testCanCreateTestCustomerRow(self):
        for customderId in range(15):
            row = dev_test.createTestCustomerRow(customderId)
            self.assertTrue(row is not None)
            self.assertEqual(len(row), 6)

    def testCanQueryVersion(self):
        # Simply exercise these functions, their results do not really matter.
        _tools.platformVersion()
        _tools.pythonVersion()

    def testCanValidatePythonName(self):
        self.assertEqual(_tools.validatedPythonName("x", "abc_123"), "abc_123")
        self.assertEqual(_tools.validatedPythonName("x", " abc_123 "), "abc_123")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "1337")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", " ")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "a.b")

    def testCanBuildHumanReadableList(self):
        self.assertEqual(_tools.humanReadableList([]), "")
        self.assertEqual(_tools.humanReadableList(["a"]), "'a'")
        self.assertEqual(_tools.humanReadableList(["a", "b"]), "'a' or 'b'")
        self.assertEqual(_tools.humanReadableList(["a", "b", "c"]), "'a', 'b' or 'c'")

    def _testWithSuffix(self, expectedPath, pathToTest, suffixToTest):
        actualPath = _tools.withSuffix(pathToTest, suffixToTest)
        self.assertEqual(expectedPath, actualPath)

    def testCanBuildNameWithSuffix(self):
        self._testWithSuffix("hugo.pas", "hugo.txt", ".pas")
        self._testWithSuffix("hugo", "hugo.txt", "")
        self._testWithSuffix("hugo.", "hugo.txt", ".")
        self._testWithSuffix("hugo.txt", "hugo", ".txt")
        self._testWithSuffix(os.path.join("eggs", "hugo.pas"), os.path.join("eggs", "hugo.txt"), ".pas")

    def testCanAsciifyText(self):
        self.assertEqual(_tools.asciified("hello"), "hello")
        self.assertEqual(_tools.asciified("h\xe4ll\xf6"), "hallo")
        self.assertEqual(_tools.asciified("hello.world!"), "hello.world!")

    def testFailAsciifyOnNonUnicode(self):
        self.assertRaises(ValueError, _tools.asciified, b"hello")
        self.assertRaises(ValueError, _tools.asciified, 17)

    def testCanNamifyText(self):
        self.assertEqual(_tools.namified("hello"), "hello")
        self.assertEqual(_tools.namified("hElLo"), "hElLo")
        self.assertEqual(_tools.namified("h3LL0"), "h3LL0")
        self.assertEqual(_tools.namified("Date of birth"), "Date_of_birth")
        self.assertEqual(_tools.namified("a    b"), "a_b")

    def testCanNamifyNumber(self):
        self.assertEqual(_tools.namified("1a"), "x1a")
        self.assertEqual(_tools.namified("3.1415"), "x3_1415")

    def testCanNamifyKeyword(self):
        self.assertEqual(_tools.namified("if"), "if_")

    def testCanNamifyEmptyText(self):
        self.assertEqual(_tools.namified(""), "x")
        self.assertEqual(_tools.namified(" "), "x")
        self.assertEqual(_tools.namified("\t"), "x")

    def testCanNamifyControlCharacters(self):
        self.assertEqual(_tools.namified("\r"), "x")
        self.assertEqual(_tools.namified("a\rb"), "a_b")


class NumberedTest(unittest.TestCase):
    def testCanDetectNoneNumber(self):
        self.assertEqual(_tools.numbered("123abc"), (None, False, "123abc"))
        self.assertEqual(_tools.numbered("01.02.2014"), (None, False, "01.02.2014"))

    def testCanDetectInteger(self):
        self.assertEqual(_tools.numbered("123"), (_tools.NUMBER_INTEGER, False, 123))

    def testCanDetectDecimalWithPoint(self):
        self.assertEqual(_tools.numbered("123.45"), (_tools.NUMBER_DECIMAL_POINT, False, decimal.Decimal("123.45")))
        self.assertEqual(_tools.numbered("123,456.78"), (_tools.NUMBER_DECIMAL_POINT, True, decimal.Decimal("123456.78")))

    def testCanDetectDecimalWithComma(self):
        actual = _tools.numbered("123,45", decimalSeparator=",", thousandsSeparator=".")
        expected = (_tools.NUMBER_DECIMAL_COMMA, False, decimal.Decimal("123.45"))
        self.assertEqual(actual, expected)
        actual = _tools.numbered("123.456,78", decimalSeparator=",", thousandsSeparator=".")
        expected = (_tools.NUMBER_DECIMAL_COMMA, True, decimal.Decimal("123456.78"))
        self.assertEqual(actual, expected)


class RowsTest(unittest.TestCase):
    def test_can_read_excel_rows(self):
        excel_path = dev_test.getTestInputPath('valid_customers.xls')
        row_count = len(list(_tools.excel_rows(excel_path)))
        self.assertTrue(row_count > 0)

    def test_can_read_ods_rows(self):
        ods_path = dev_test.getTestIcdPath('customers.ods')
        ods_rows = list(_tools.ods_rows(ods_path))
        self.assertTrue(len(ods_rows) > 0)
        none_empty_rows = [row for row in ods_rows if len(row) > 0]
        self.assertTrue(len(none_empty_rows) > 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
