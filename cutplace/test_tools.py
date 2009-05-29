"""
Test for `tools` module.
"""
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