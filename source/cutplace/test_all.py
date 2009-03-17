"""Test suite for all test cases."""
import logging
import test_cutplace
import test_data
import test_icd
import test_fields
import test_parsers
import unittest

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    
    loader = unittest.TestLoader()
    
    # TODO: Automatically discover test cases.
    # TODO: Call sys-exit(1) in case any test fails.
    for testCaseClass in [
                        test_cutplace.CutplaceTest,
                        test_icd.InterfaceControlDocumentTest,
                        test_data.DataFormatTest,
                        test_fields.AbstractFieldFormatTest,
                        test_fields.ChoiceFieldFormatTest,
                        test_fields.DateTimeFieldFormatTest,
                        test_fields.IntegerFieldFormatTest,
                        test_fields.PatternFieldFormatTest,
                        test_fields.RegExFieldFormatTest,
                        test_parsers.DelimitedParserTest]:
        suite = loader.loadTestsFromTestCase(testCaseClass)
        unittest.TextTestRunner(verbosity=2).run(suite)
