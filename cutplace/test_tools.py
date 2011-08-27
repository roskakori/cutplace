"""
Test for `tools` module.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
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
import os.path
import StringIO
import unittest

import dev_test
import tools
import _tools


class ToolsTest(unittest.TestCase):
    """TestCase for tools module."""

    def testCreateTestDateTime(self):
        for _ in range(15):
            dateTime = dev_test.createTestDateTime()
            self.assertTrue(dateTime is not None)
            self.assertNotEqual(dateTime, "")

    def testCreateTestName(self):
        for _ in range(15):
            name = dev_test.createTestName()
            self.assertTrue(name is not None)
            self.assertNotEqual(name, "")

    def testCreateTestCustomerRow(self):
        for customderId in range(15):
            row = dev_test.createTestCustomerRow(customderId)
            self.assertTrue(row is not None)
            self.assertEqual(len(row), 6)

    def testVersion(self):
        # Simply exercise these functions, their results do not really matter.
        _tools.platformVersion()
        _tools.pythonVersion()

    def testValidatedPythonName(self):
        self.assertEqual(_tools.validatedPythonName("x", "abc_123"), "abc_123")
        self.assertEqual(_tools.validatedPythonName("x", " abc_123 "), "abc_123")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "1337")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", " ")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "a.b")

    def testHumanReadableList(self):
        self.assertEqual(_tools.humanReadableList([]), "")
        self.assertEqual(_tools.humanReadableList(["a"]), "'a'")
        self.assertEqual(_tools.humanReadableList(["a", "b"]), "'a' or 'b'")
        self.assertEqual(_tools.humanReadableList(["a", "b", "c"]), "'a', 'b' or 'c'")

    def _testWithSuffix(self, expectedPath, pathToTest, suffixToTest):
        actualPath = _tools.withSuffix(pathToTest, suffixToTest)
        self.assertEqual(expectedPath, actualPath)

    def testWithSuffix(self):
        self._testWithSuffix("hugo.pas", "hugo.txt", ".pas")
        self._testWithSuffix("hugo", "hugo.txt", "")
        self._testWithSuffix("hugo.", "hugo.txt", ".")
        self._testWithSuffix("hugo.txt", "hugo", ".txt")
        self._testWithSuffix(os.path.join("eggs", "hugo.pas"), os.path.join("eggs", "hugo.txt"), ".pas")

    def testInputLocation(self):
        location = tools.InputLocation("eggs.txt", hasColumn=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (1;1)")
        location.advanceColumn(3)
        self.assertEqual(location.column, 3)
        location.advanceColumn()
        self.assertEqual(location.column, 4)
        location.advanceLine()
        self.assertEqual(location.line, 1)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (2;1)")

        # Test input with cells.
        location = tools.InputLocation("eggs.csv", hasCell=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.cell, 0)
        self.assertEqual(str(location), "eggs.csv (R1C1)")
        location.advanceLine()
        location.advanceCell(17)
        self.assertEqual(str(location), "eggs.csv (R2C18)")

        # Test input with sheet.
        location = tools.InputLocation("eggs.ods", hasCell=True, hasSheet=True)
        self.assertEqual(str(location), "eggs.ods (Sheet1!R1C1)")
        location.advanceSheet()
        location.advanceLine()
        location.advanceCell(17)
        self.assertEqual(str(location), "eggs.ods (Sheet2!R2C18)")

        # Test StringIO input.
        inputStream = StringIO.StringIO("hugo was here")
        location = tools.InputLocation(inputStream)
        self.assertEqual(str(location), "<io> (1)")

    def testCanAsciifyText(self):
        self.assertEqual(_tools.asciified(u"hello"), u"hello")
        self.assertEqual(_tools.asciified(u"h\xe4ll\xf6"), u"hallo")
        self.assertEqual(_tools.asciified(u"hello.world!"), u"hello.world!")

    def testFailAsciifyOnNonUnicode(self):
        self.assertRaises(ValueError, _tools.asciified, "hello")
        self.assertRaises(ValueError, _tools.asciified, 17)

    def testCanNamifyText(self):
        self.assertEqual(_tools.namified(u"hello"), "hello")
        self.assertEqual(_tools.namified(u"hElLo"), "hElLo")
        self.assertEqual(_tools.namified(u"h3LL0"), "h3LL0")
        self.assertEqual(_tools.namified(u"Date of birth"), "Date_of_birth")
        self.assertEqual(_tools.namified(u"a    b"), "a_b")

    def testCanNamifyNumber(self):
        self.assertEqual(_tools.namified(u"1a"), "x1a")
        self.assertEqual(_tools.namified(u"3.1415"), "x3_1415")

    def testCanNamifyKeyword(self):
        self.assertEqual(_tools.namified(u"if"), "if_")

    def testCanNamifyEmptyText(self):
        self.assertEqual(_tools.namified(u""), "x")
        self.assertEqual(_tools.namified(u" "), "x")
        self.assertEqual(_tools.namified(u"\t"), "x")

    def testCanNamifyControlCharacters(self):
        self.assertEqual(_tools.namified(u"\r"), "x")
        self.assertEqual(_tools.namified(u"a\rb"), "a_b")

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
