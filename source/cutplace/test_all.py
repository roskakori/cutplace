"""Test suite for all test cases."""
import logging
import test_checks
import test_cutplace
import test_data
import test_interface
import test_fields
import test_parsers
import test_tools
import test_web
import unittest

def main():
    loader = unittest.TestLoader()
    
    # TODO: Automatically discover test cases.
    # TODO: Call sys-exit(1) in case any test fails.
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
                        test_tools.ToolsTest
                        # FIXME: Stop server and add: test_web.WebTest
                        ]:
        suite = loader.loadTestsFromTestCase(testCaseClass)
        unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    main()
