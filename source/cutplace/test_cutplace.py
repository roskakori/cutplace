"""Tests  for cutplace application."""
import cutplace
import logging
import os.path
import tools
import unittest

class CutplaceTest(unittest.TestCase):
    """Test cases for cutplace command line interface."""

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
        testsInputFolder = tools.getTestFolder("input")
        validCsvFileNames = tools.listdirMatching(testsInputFolder, VALID_PREFIX + ".*\\.csv")
        validCsvPaths = list(os.path.join(testsInputFolder, fileName) for fileName in validCsvFileNames)
        for dataPath in validCsvPaths:
            # Get file name without "valid
            baseFileName = os.path.basename(dataPath)
            baseFileNameWithoutCsvSuffix = os.path.splitext(baseFileName)[0]
            baseFileNameWithoutValidPrefixAndCsvSuffix = baseFileNameWithoutCsvSuffix[len(VALID_PREFIX):]
            icdBaseName = baseFileNameWithoutValidPrefixAndCsvSuffix.split("_")[0]
            # FIXME: Rename test/input/idcs to icds.
            icdFolder = os.path.join(testsInputFolder, "icds")
            icdPath = os.path.join(icdFolder, icdBaseName + ".csv")
            cutPlace = cutplace.CutPlace()
            cutPlace.setOptions([icdPath, dataPath])
            # TODO: Assert number of errors detected in dataPath is 0.
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
