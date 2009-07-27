"""
Test suite for all test cases.
"""
import logging
import sys
import test_checks
import test_cutplace
import test_data
import test_interface
import test_fields
import test_ods
import test_parsers
import test_range
import test_tools
import test_web
import unittest
import checks
import cutplace
import data
import doctest
import fields
import interface
import ods
import parsers
import range
import tools
import version
import web

def createTestSuite():
    """
    TestSuite including all unit tests and doctests found in the source code.
    """
    result = unittest.TestSuite()
    loader = unittest.TestLoader()

    # TODO: Automatically discover doctest cases.
    for module in checks, cutplace, data, fields, interface, ods, parsers, range, tools, version, web:
        result.addTest(doctest.DocTestSuite(module))    

    # TODO: Automatically discover test cases.
    allTests = [
            test_checks.DistinctCountCheckTest,
            test_checks.IsUniqueCheckTest,
            test_cutplace.CutplaceTest,
            test_data.DataFormatTest,
            test_interface.InterfaceControlDocumentTest,
            test_fields.AbstractFieldFormatTest,
            test_fields.ChoiceFieldFormatTest,
            test_fields.DateTimeFieldFormatTest,
            test_fields.DecimalFieldFormatTest,
            test_fields.IntegerFieldFormatTest,
            test_fields.PatternFieldFormatTest,
            test_fields.RegExFieldFormatTest,
            test_ods.OdsTest,
            test_parsers.DelimitedParserTest,
            test_parsers.ExcelReaderTest,
            test_parsers.FixedParserTest,
            test_range.RangeTest,
            test_tools.ToolsTest
            # FIXME: Stop server and add: test_web.WebTest
            ]
    for testCaseClass in allTests:
        result.addTest(loader.loadTestsFromTestCase(testCaseClass))
    
    return result
    
def main():
    """
    Run all tests.
    """
    testCount = 0
    errorCount = 0
    failureCount = 0

    allTestSuite = createTestSuite()
    testResults = unittest.TextTestRunner(verbosity=2).run(allTestSuite)
    testCount += testResults.testsRun
    failureCount += len(testResults.failures)
    errorCount += len(testResults.errors)
    print "test_all: ran %d tests with %d failures and %d errors" % (testCount, failureCount, errorCount)
    if (errorCount + failureCount) > 0:
        sys.exit(1)
    
if __name__ == '__main__': # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    main()
