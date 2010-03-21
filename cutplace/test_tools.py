"""
Test for `tools` module.
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
import dev_test
import os.path
import tools
import unittest

class ToolsTest(unittest.TestCase):
    """TestCase for tools module."""

    def testCreateTestDateTime(self):
        for i in range(15):
            dateTime = tools.createTestDateTime()
            self.assertTrue(dateTime is not None)
            self.assertNotEqual(dateTime, "")

    def testCreateTestName(self):
        for i in range(15):
            name = tools.createTestName()
            self.assertTrue(name is not None)
            self.assertNotEqual(name, "")

    def testCreateTestCustomerRow(self):
        for customderId in range(15):
            row = dev_test.createTestCustomerRow(customderId)
            self.assertTrue(row is not None)
            self.assertEqual(len(row), 6)

    def testVersion(self):
        # Simply exercise these functions, their results do not really matter.
        tools.platformVersion()
        tools.pythonVersion()
        
    def testValidatedPythonName(self):
        self.assertEqual(tools.validatedPythonName("x", "abc_123"), "abc_123")
        self.assertEqual(tools.validatedPythonName("x", " abc_123 "), "abc_123")
        self.assertRaises(NameError, tools.validatedPythonName, "x", "1337")
        self.assertRaises(NameError, tools.validatedPythonName, "x", "")
        self.assertRaises(NameError, tools.validatedPythonName, "x", " ")
        self.assertRaises(NameError, tools.validatedPythonName, "x", "a.b")
        
    def testHumanReadableList(self):
        self.assertEqual(tools.humanReadableList([]), "")
        self.assertEqual(tools.humanReadableList(["a"]), "'a'")
        self.assertEqual(tools.humanReadableList(["a", "b"]), "'a' or 'b'")
        self.assertEqual(tools.humanReadableList(["a", "b", "c"]), "'a', 'b' or 'c'")

    def _testWithSuffix(self, expectedPath, pathToTest, suffixToTest):
        actualPath = tools.withSuffix(pathToTest, suffixToTest)
        self.assertEqual(expectedPath, actualPath)

    def testWithSuffix(self):
        self._testWithSuffix("hugo.pas", "hugo.txt", ".pas")
        self._testWithSuffix("hugo", "hugo.txt", "")
        self._testWithSuffix("hugo.", "hugo.txt", ".")
        self._testWithSuffix("hugo.txt", "hugo", ".txt")
        self._testWithSuffix(os.path.join("eggs", "hugo.pas"), os.path.join("eggs", "hugo.txt"), ".pas")
        
if __name__ == "__main__": # pragma: no cover
    unittest.main()