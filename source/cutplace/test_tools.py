import dev_test
import tools
import unittest

class ToolsTest(unittest.TestCase):
    """TestCase for tools module."""

    def testCreateTestDateTime(self):
        for i in range(0, 15):
            dateTime = tools.createTestDateTime()
            self.assertTrue(dateTime is not None)
            self.assertNotEqual(dateTime, "")

    def testCreateTestName(self):
        for i in range(0, 15):
            name = tools.createTestName()
            self.assertTrue(name is not None)
            self.assertNotEqual(name, "")

    def testCreateTestCustomerRow(self):
        for customderId in range(0, 15):
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
        
if __name__ == "__main__":
    unittest.main()