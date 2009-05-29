'''
Tests for ODS.
'''
import dev_test
import logging
import ods
import unittest

class OdsTest(unittest.TestCase):

    def testConvertToCsv(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from_ods.csv")
        ods.main([testInPath, testOutPath])

    def testConvertToDocBook(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from_ods.xml")
        ods.main(["--format=docbook", testInPath, testOutPath])

    def testConvertToRst(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from_ods.rst")
        ods.main(["--format=rst", testInPath, testOutPath])

    def testBrokenKinkyFileName(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("kinky_file_name//\\:^$\\::/")
        self.assertRaises(SystemExit, ods.main, [testInPath, testOutPath])

    def testBrokenNoOptionsAtAll(self):
        self.assertRaises(SystemExit, ods.main, [])

    def testBrokenSheet(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from_ods.csv")
        self.assertRaises(SystemExit, ods.main, ["--sheet=x", testInPath, testOutPath])
        self.assertRaises(SystemExit, ods.main, ["--sheet=0", testInPath, testOutPath])
        # FIXME: Report error when sheet is out of range: self.assertRaises(SystemExit, ods.main, ["--sheet=17", testInPath, testOutPath])

if __name__ == "__main__": # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    logging.getLogger("cutplace.ods").setLevel(logging.INFO)
    unittest.main()