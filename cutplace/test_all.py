"""
Test suite for all test cases.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
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
import doctest
import logging
import os.path
import sys
import unittest

from . import checks
from . import data
from . import fields
from . import interface
from . import ranges
from . import sniff
from . import errors
from . import version
from . import test_checks
from . import test_cutplace
from . import test_data
from . import test_interface
from . import test_fields
from . import test_ods
from . import test_parsers
from . import test_ranges
from . import test_sniff
from . import test_tools
from . import test_web
from . import _cutplace
from . import _ods
from . import _parsers
from . import _tools
from . import _web


def createTestSuite():
    """
    TestSuite including all unit tests and doctests found in the source code.
    """
    result = unittest.TestSuite()
    loader = unittest.TestLoader()

    # TODO: Automatically discover doctest cases.
    for module in checks, data, fields, interface, ranges, sniff, errors, version, _cutplace, _ods, _parsers, _tools, _web:
        result.addTest(doctest.DocTestSuite(module))
    result.addTest(doctest.DocFileSuite(os.path.join("docs", "api.rst"), module_relative=False))

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
            test_ranges.RangeTest,
            test_sniff.SniffTest,
            test_tools.ToolsTest
            # FIXME: Stop server and add: test_web.WebTest
            ]
    for testCaseClass in allTests:
        result.addTest(loader.loadTestsFromTestCase(testCaseClass))

    return result


def main(argv=None):
    """
    Run all tests.
    """
    if argv is None:
        argv = sys.argv
    assert argv

    result = 1

    testCount = 0
    errorCount = 0
    failureCount = 0

    allTestSuite = createTestSuite()
    testResults = unittest.TextTestRunner(verbosity=2).run(allTestSuite)
    testCount += testResults.testsRun
    failureCount += len(testResults.failures)
    errorCount += len(testResults.errors)
    print("test_all: ran %d tests with %d failures and %d errors" % (testCount, failureCount, errorCount))
    if (errorCount + failureCount) == 0:
        result = 0
    return result

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    sys.exit(main())
