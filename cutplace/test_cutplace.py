"""
Tests  for cutplace application.
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
import cutplace
import dev_test
import logging
import optparse
import os.path
import parsers
import tools
import unittest

_log = logging.getLogger("cutplace")

class CutplaceTest(unittest.TestCase):
    """Test cases for cutplace command line interface."""

    def testVersion(self):
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutplace.main, ["--version"])
        
    def testHelp(self):
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutplace.main, ["--help"])
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutplace.main, ["-h"])

    def testListEncodings(self):
        cutplace.main(["--list-encodings"])

    # TODO: Add tests for broken CSV files.
    # TODO: Add test for continued processing of multiple data files in case the first has a Unicode encoding error.

    def testSplitValidData(self):
        icdPath = dev_test.getTestIcdPath("customers.ods")
        dataPath = dev_test.getTestInputPath("valid_customers_iso-8859-1.csv")
        cutplace.main(["--split", icdPath, dataPath])
        acceptedDataPath = dev_test.getTestInputPath("valid_customers_iso-8859-1_accepted.csv")
        rejectedDataPath = dev_test.getTestInputPath("valid_customers_iso-8859-1_rejected.txt")
        self.assertNotEqual(os.path.getsize(acceptedDataPath), 0)
        self.assertEqual(os.path.getsize(rejectedDataPath), 0)
        os.remove(acceptedDataPath)
        os.remove(rejectedDataPath)
        
    def testSplitBrokenData(self):
        icdPath = dev_test.getTestIcdPath("customers.ods")
        dataPath = dev_test.getTestInputPath("broken_customers.csv")
        try:
            cutplace.main(["--split", icdPath, dataPath])
            self.fail("expected SystemExit error")
        except SystemExit, error:
            self.assertEquals(error.code, 1)
        acceptedDataPath = dev_test.getTestInputPath("broken_customers_accepted.csv")
        rejectedDataPath = dev_test.getTestInputPath("broken_customers_rejected.txt")
        self.assertNotEqual(os.path.getsize(acceptedDataPath), 0)
        self.assertNotEqual(os.path.getsize(rejectedDataPath), 0)
        os.remove(acceptedDataPath)
        os.remove(rejectedDataPath)
        
    def _testValidIcd(self, suffix):
        assert suffix is not None
        icdPath = dev_test.getTestIcdPath("customers." + suffix)
        cutPlace = cutplace.CutPlace()
        cutPlace.setIcdFromFile(icdPath)
    
    def testValidIcdInCsvFormat(self):
        self._testValidIcd("csv")
    
    def testValidIcdInOdsFormat(self):
        self._testValidIcd("ods")
    
    def testValidIcdInXlsFormat(self):
        try:
            self._testValidIcd("xls")
        except parsers.CutplaceXlrdImportError:
            _log.warning("skipped test due lack of xlrd module")

    def testValidCsvs(self):
        VALID_PREFIX = "valid_"
        testsInputFolder = dev_test.getTestFolder("input")
        validCsvFileNames = tools.listdirMatching(testsInputFolder, VALID_PREFIX + ".*\\.csv")
        validCsvPaths = list(os.path.join(testsInputFolder, fileName) for fileName in validCsvFileNames)
        for dataPath in validCsvPaths:
            # Compute the base name of the related ICD.
            baseFileName = os.path.basename(dataPath)
            baseFileNameWithoutCsvSuffix = os.path.splitext(baseFileName)[0]
            baseFileNameWithoutValidPrefixAndCsvSuffix = baseFileNameWithoutCsvSuffix[len(VALID_PREFIX):]
            # Compute the full path of the related ICD.
            icdBaseName = baseFileNameWithoutValidPrefixAndCsvSuffix.split("_")[0]
            icdPath = dev_test.getTestIcdPath(icdBaseName + ".csv")
            # Now validate the data.
            cutplace.main([icdPath, dataPath])
            # TODO: Assert number of errors detected in dataPath is 0.

    def testValidFixedTxt(self):
        icdPath = dev_test.getTestIcdPath("customers_fixed.ods")
        dataPath = dev_test.getTestInputPath("valid_customers_fixed.txt")
        cutplace.main([icdPath, dataPath])
        # TODO: Assert number of errors detected in dataPath is 0.

    def testValidNativeExcelFormats(self):
        icdPath = dev_test.getTestIcdPath("native_excel_formats.ods")
        dataPath = dev_test.getTestInputPath("valid_native_excel_formats.xls")
        cutplace.main([icdPath, dataPath])
        # TODO: Assert number of errors detected in dataPath is 0.

    def testBrokenUnknownCommandLineOption(self):
        self.assertRaises(optparse.OptionError, cutplace.main, ["--no-such-option"])

    def testBrokenNoCommandLineOptions(self):
        self.assertRaises(optparse.OptionError, cutplace.main, [])

    def testBrokenNonExistentIcdPath(self):
        self.assertRaises(IOError, cutplace.main, ["no-such-icd.nix"])
        
    def testBrokenNonExistentDataPath(self):
        icdPath = dev_test.getTestIcdPath("customers.ods")
        self.assertRaises(EnvironmentError, cutplace.main, [icdPath, "no-such-data.nix"])

class LotsOfCustomersTest(unittest.TestCase):
    """Test case for performance profiling."""

    def testLotsOfCustomersCsv(self):
        icdOdsPath = dev_test.getTestIcdPath("customers.ods")
        locCsvPath = dev_test.getTestFile("input", "lots_of_customers.csv")
        dev_test.createLotsOfCustomersCsv(locCsvPath)
        cutplace.main([icdOdsPath, locCsvPath])
        # TODO: Assert number of errors detected in dataPath is 0.
        
if __name__ == '__main__': # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    unittest.main()
