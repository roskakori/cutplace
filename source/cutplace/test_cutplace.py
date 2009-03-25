"""Tests  for cutplace application."""
import cutplace
import logging#
import os.path
import re
import sys
import unittest

class CutplaceTest(unittest.TestCase):
    """Test cases for cutplace command line interface."""
    def listdirMatching(self, folder, pattern):
        """Yield name of entries in folder that match regex pattern."""
        regex = re.compile(pattern)
        for entry in os.listdir(folder):
            if regex.match(entry):
                yield entry

    def getTestFolder(self, folder):
        assert folder
        
        testFolder = os.path.join(os.getcwd(), "tests")
        if not os.path.exists(testFolder):
            raise IOError("test must run from project folder in order to find test files; currently attempting to find them in: %r" % testFolder)
        result = os.path.join(testFolder, folder)
        return result
        
    def getTestFile(self, folder, fileName):
        assert folder
        assert fileName
        
        result = os.path.join(getTestFolder(folder), fileName)
        return result
         
    def testVersion(self):
        cutPlace = cutplace.CutPlace()
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutPlace.setOptions, ["--version"])
        
    def testHelp(self):
        cutPlace = cutplace.CutPlace()
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutPlace.setOptions, ["--help"])
        self.assertRaises(cutplace.ExitQuietlyOptionError, cutPlace.setOptions, ["-h"])

    def testListEncodings(self):
        cutPlace = cutplace.CutPlace()
        cutPlace.setOptions(["--list-encodings"])

    # TODO: Add tests for broken CSV files.
    
    def testValidCsvs(self):
        VALID_PREFIX = "valid_"
        testsInputFolder = self.getTestFolder("input")
        validCsvFileNames = self.listdirMatching(testsInputFolder, VALID_PREFIX + ".*\\.csv")
        validCsvPaths = list(os.path.join(testsInputFolder, fileName) for fileName in validCsvFileNames)
        for dataPath in validCsvPaths:
            # Get file name without "valid
            baseFileName = os.path.basename(dataPath)
            baseFileNameWithoutCsvSuffix = os.path.splitext(baseFileName)[0]
            baseFileNameWithoutValidPrefixAndCsvSuffix = baseFileNameWithoutCsvSuffix[len(VALID_PREFIX):]
            icdBaseName = baseFileNameWithoutValidPrefixAndCsvSuffix.split("_")[0]
            # FIXME: Rename test/input/idcs to icds.
            icdFolder = os.path.join(testsInputFolder, "idcs")
            icdPath = os.path.join(icdFolder, icdBaseName + ".csv")
            cutPlace = cutplace.CutPlace()
            cutPlace.setOptions([icdPath, dataPath])
            # TODO: Assert number of errors detected in dataPath is 0.
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
