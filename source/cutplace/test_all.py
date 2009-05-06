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
import test_parsers
import test_range
import test_tools
import test_web
import unittest

def main():
    loader = unittest.TestLoader()
    testCount = 0
    errorCount = 0
    failureCount = 0
    
    # TODO: Automatically discover test cases.
    for testCaseClass in [
                        test_checks.DistinctCountCheckTest,
                        test_checks.IsUniqueCheckTest,
                        test_cutplace.CutplaceTest,
                        test_data.DataFormatTest,
                        test_interface.InterfaceControlDocumentTest,
                        test_fields.AbstractFieldFormatTest,
                        test_fields.ChoiceFieldFormatTest,
                        test_fields.DateTimeFieldFormatTest,
                        test_fields.IntegerFieldFormatTest,
                        test_fields.PatternFieldFormatTest,
                        test_fields.RegExFieldFormatTest,
                        test_parsers.DelimitedParserTest,
                        test_parsers.ExcelParserTest,
                        test_parsers.FixedParserTest,
                        test_range.RangeTest,
                        test_tools.ToolsTest
                        # FIXME: Stop server and add: test_web.WebTest
                        ]:
        suite = loader.loadTestsFromTestCase(testCaseClass)
        testResults = unittest.TextTestRunner(verbosity=2).run(suite)
        testCount += testResults.testsRun
        failureCount += len(testResults.failures)
        errorCount += len(testResults.errors)
    print "test_all: Ran %d tests with %d failures and %d errors" % (testCount, failureCount, errorCount)
    if (errorCount + failureCount) > 0:
        sys.exit(1)
    
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    main()
