"""
Test for `sniff` module.
"""
# Copyright (C) 2009-2012 Thomas Aglassinger
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
from __future__ import with_statement

import unittest
import StringIO

import data
import fields
import interface
import sniff

import dev_test
import _cutsniff


class SniffTest(unittest.TestCase):
    def testCanFindOutSniffDataFormat(self):
        fileNameToExpectedFormatMap = {
            "valid_customers.csv": data.FORMAT_DELIMITED,
            "valid_customers.ods": data.FORMAT_ODS,
            "valid_customers.xls": data.FORMAT_EXCEL,
        }
        for testFileName, exptectedDataFormatName in fileNameToExpectedFormatMap.items():
            testFilePath = dev_test.getTestInputPath(testFileName)
            testFile = open(testFilePath, "rb")
            try:
                actualDataFormat = sniff.createDataFormat(testFile)
                actualDataFormatName = actualDataFormat.name
                self.assertEqual(actualDataFormatName, exptectedDataFormatName,
                    "data format for file must be %r but is %r: %r" % (exptectedDataFormatName, actualDataFormatName, testFilePath))
            finally:
                testFile.close()

    def testCanFindOutDelimitedOptions(self):
        fileNameToExpectedOptionsMap = {
            "valid_customers.csv": {
                sniff._ITEM_DELIMITER: ",",
                sniff._ESCAPE_CHARACTER: "\"",
                sniff._ENCODING: 'ascii',
                sniff._QUOTE_CHARACTER: "\""
            },
        }
        for testFileName, exptectedDelimitedOptions in fileNameToExpectedOptionsMap.items():
            testFilePath = dev_test.getTestInputPath(testFileName)
            testFile = open(testFilePath, "rb")
            try:
                actualDelimitedOptions = sniff.delimitedOptions(testFile)

                # Add actual line delimiter as expected. We cannot provide a proper expected line
                # delimiter in ``exptectedDelimitedOptions`` because the actual value depend on
                # the platform the repository has been checked out to.
                actualLineDelimiter = actualDelimitedOptions["lineDelimiter"]
                self.assertTrue(actualLineDelimiter)
                exptectedDelimitedOptions["lineDelimiter"] = actualLineDelimiter

                self.assertEqual(actualDelimitedOptions, exptectedDelimitedOptions, \
                    "data format for file must be %r but is %r: %r" % (exptectedDelimitedOptions, actualDelimitedOptions, testFilePath))
            finally:
                testFile.close()

    def testCanCreateSniffedReader(self):
        testFileNames = [
            "valid_customers.csv",
            "valid_customers.ods",
            "valid_customers.xls"
        ]
        for testFileName in testFileNames:
            testFilePath = dev_test.getTestInputPath(testFileName)
            testFile = open(testFilePath, "rb")
            try:
                reader = sniff.createReader(testFile)
                rowCount = 0
                for _ in reader:
                    rowCount += 1
                self.assertTrue(rowCount > 0)
            finally:
                testFile.close()

    def testCanCreateSniffedReaderForEmptyData(self):
        emptyReadable = StringIO.StringIO("")

        self.assertTrue(sniff.delimitedOptions(emptyReadable))

        emptyDataFormat = sniff.createDataFormat(emptyReadable)
        self.assertTrue(emptyDataFormat)
        self.assertEqual(emptyDataFormat.name, data.FORMAT_DELIMITED)

        emptyReader = sniff.createReader(emptyReadable)
        self.assertTrue(emptyReadable)
        rowCount = 0
        for _ in emptyReader:
            rowCount += 1
        self.assertEqual(rowCount, 0)

    def testFailsToCreateEmptyInterfaceControlDocument(self):
        emptyReadable = StringIO.StringIO("")
        self.assertRaises(sniff.CutplaceSniffError, sniff.createCidRows, emptyReadable)

    def testCanCreateInterfaceControlDocument(self):
        def assertFieldTypeEquals(cidRows, fieldName, typeName):
            fieldRowIndex = None
            rowToExamineIndex = 0
            while (rowToExamineIndex < len(cidRows)) and (fieldRowIndex is None):
                cidRowToExamine = cidRows[rowToExamineIndex]
                if (len(cidRowToExamine) >= 6) and (cidRowToExamine[0] == u"f") and (cidRowToExamine[1] == fieldName):
                    fieldRowIndex = rowToExamineIndex
                else:
                    rowToExamineIndex += 1
            assert fieldRowIndex is not None, "field must be found in cid rows: %r <-- %s" % (fieldName, cidRows)
            typeNameFromCidRow = cidRowToExamine[5]
            self.assertEqual(typeName, typeNameFromCidRow)

        testFileNames = [
            "valid_customers.csv",
            "valid_customers.ods",
            "valid_customers.xls"
        ]
        for testFileName in testFileNames:
            testFilePath = dev_test.getTestInputPath(testFileName)
            testFile = open(testFilePath, "rb")
            try:
                cidRows = sniff.createCidRows(testFile)
                assertFieldTypeEquals(cidRows, u"column_a", u"Integer")  # branch
                assertFieldTypeEquals(cidRows, u"column_c", u"Text")  # first name
                assertFieldTypeEquals(cidRows, u"column_f", u"Text")  # date of birth
            finally:
                testFile.close()

    def testHeaderAndStopAfter(self):
        testFileNames = [
            "valid_customers.csv",
            "valid_customers.ods",
            "valid_customers.xls"
        ]
        for testFileName in testFileNames:
            testFilePath = dev_test.getTestInputPath(testFileName)
            testFile = open(testFilePath, "rb")
            try:
                reader = sniff.createReader(testFile)
                rowCount = 0
                for _ in reader:
                    rowCount += 1
                self.assertTrue(rowCount > 0)
            finally:
                testFile.close()

    def testCanSniffStandardFieldFormats(self):
        testFilePath = dev_test.getTestInputPath("valid_alltypes.csv")
        with open(testFilePath, "rb") as testFile:
            cid = sniff.createCid(testFile, header=1)
            self.assertEqual(cid.fieldNames, [u'customer_id', u'short_name', u'gender', u'date_of_birth', u'balance'])
            self.assertEqual(cid.fieldFormatFor('customer_id').__class__, fields.IntegerFieldFormat)
            self.assertEqual(cid.fieldFormatFor('short_name').__class__, fields.TextFieldFormat)
            self.assertEqual(cid.fieldFormatFor('gender').__class__, fields.TextFieldFormat)
            self.assertEqual(cid.fieldFormatFor('date_of_birth').__class__, fields.TextFieldFormat)
            self.assertEqual(cid.fieldFormatFor('balance').__class__, fields.DecimalFieldFormat)


class SniffMainTest(unittest.TestCase):
    def testCanSniffAndValidateUsingMain(self):
        testIcdPath = dev_test.getTestOutputPath("icd_sniffed_valid_customers.csv")
        testDataPath = dev_test.getTestInputPath("valid_customers.csv")
        exitCode = _cutsniff.main(["test", testIcdPath, testDataPath])
        self.assertEqual(exitCode, 0)
        sniffedIcd = interface.InterfaceControlDocument()
        sniffedIcd.read(testIcdPath)
        for _ in interface.validatedRows(sniffedIcd, testDataPath):
            pass

    def testCanSniffAndValidateUsingMainWithFieldNames(self):
        testIcdPath = dev_test.getTestOutputPath("icd_sniffed_valid_customers.csv")
        testDataPath = dev_test.getTestInputPath("valid_customers.csv")
        exitCode = _cutsniff.main(["test", "--names", " branchId,customerId, firstName,surName ,gender,dateOfBirth ", testIcdPath, testDataPath])
        self.assertEqual(exitCode, 0)
        sniffedIcd = interface.InterfaceControlDocument()
        sniffedIcd.read(testIcdPath)
        self.assertEqual(sniffedIcd.fieldNames, ["branchId", "customerId", "firstName", "surName", "gender", "dateOfBirth"])
        for _ in interface.validatedRows(sniffedIcd, testDataPath):
            pass

    def testCanSniffAndValidateUsingMainWithHeaderAndEncoding(self):
        testIcdPath = dev_test.getTestOutputPath("icd_sniffed_valid_customers_with_header_iso-8859-15.csv")
        testDataPath = dev_test.getTestInputPath("valid_customers_with_header_iso-8859-15.csv")
        exitCode = _cutsniff.main(["test", "--data-encoding", "iso-8859-15", "--head", "1", testIcdPath, testDataPath])
        self.assertEqual(exitCode, 0)
        sniffedIcd = interface.InterfaceControlDocument()
        sniffedIcd.read(testIcdPath)
        for _ in interface.validatedRows(sniffedIcd, testDataPath):
            pass

    def testCanSniffAndValidateUsingMainWithHeaderAndSpecifiedFieldNames(self):
        testIcdPath = dev_test.getTestOutputPath("icd_sniffed_valid_customers_with_header_iso-8859-15.csv")
        testDataPath = dev_test.getTestInputPath("valid_customers_with_header_iso-8859-15.csv")
        exitCode = _cutsniff.main(["test", "--data-encoding", "iso-8859-15", "--head", "1", "--names", " branchId,customerId, firstName,surName ,gender,dateOfBirth ", testIcdPath, testDataPath])
        self.assertEqual(exitCode, 0)
        sniffedIcd = interface.InterfaceControlDocument()
        sniffedIcd.read(testIcdPath)
        self.assertEqual(sniffedIcd.fieldNames, ["branchId", "customerId", "firstName", "surName", "gender", "dateOfBirth"])
        for _ in interface.validatedRows(sniffedIcd, testDataPath):
            pass

if __name__ == "__main__":
    import logging
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    unittest.main()
