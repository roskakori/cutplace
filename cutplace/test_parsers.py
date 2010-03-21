# -*- coding: iso-8859-15 -*-
"""
Tests for parsers.
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
import dev_test
import logging
import os
import parsers
import StringIO
import tools
import types
import unittest

_log = logging.getLogger("cutplace.test_parsers")
        
class AbstractParserTest(unittest.TestCase):
    """
    Abstract TestCase acting as base for the other test cases in this module.
    """
    def possiblyStringIoedReadable(self, readable):
        if isinstance(readable, types.StringTypes):
            result = StringIO.StringIO(readable)
        else:
            result = readable
        return result

    def readAndAssertEquals(self, expectedRows, reader):
        rows = []
        for row in reader:
            for item in row:
                self.assertFalse(isinstance(item, str), "item must not be plain string: %r" % item)
            rows.append(row)
        self.assertEqual(rows, expectedRows)

class ExcelReaderTest(unittest.TestCase):

    def testIcdCustomersXls(self):
        icdCustomersIcdXlsPath = dev_test.getTestIcdPath("customers.xls")
        readable = open(icdCustomersIcdXlsPath, "rb")
        try:
            for row in parsers.excelReader(readable):
                self.assertTrue(row is not None)
                self.assertTrue(len(row))
        except parsers.CutplaceXlrdImportError:
            _log.warning("ignored ImportError caused by missing xlrd")
        finally:
            readable.close()
            
    def testCellValue(self):
        fieldTypesXlsPath = dev_test.getTestInputPath("fieldtypes.xls")
        readable = open(fieldTypesXlsPath, "rb")
        try:
            titleRowSkipped = False
            for row in parsers.excelReader(readable):
                self.assertTrue(row is not None)
                self.assertTrue(len(row) == 3, "row=%r" % row)
                if titleRowSkipped:
                    self.assertEqual(row[1], row[2], "row=%r" % row)
                else:
                    titleRowSkipped = True
        except parsers.CutplaceXlrdImportError:
            _log.warning("ignored ImportError caused by missing xlrd")
        finally:
            readable.close()
            
class FixedParserTest(AbstractParserTest):
    _DEFAULT_FIELD_LENGTHS = [5, 4, 10]
        
    def _testParse(self, expectedRows, readable, fieldLengths=_DEFAULT_FIELD_LENGTHS):
        assert expectedRows is not None
        assert readable is not None
        assert fieldLengths is not None
        
        actualReadable = self.possiblyStringIoedReadable(readable)
        reader = parsers.fixedReader(actualReadable, fieldLengths)
        self.readAndAssertEquals(expectedRows, reader)

    def testEmpty(self):
        self._testParse([], u"")

    def testValid(self):
        self._testParse([[u"38000", u" 123", u"Doe       "]], u"38000 123Doe       ")
        
    def testBrokenEndingTooSoon(self):
        self.assertRaises(parsers.ParserSyntaxError, self._testParse, [], u"38000 123Doe  ")
    
class DelimitedParserTest(AbstractParserTest):
    """
    TestCase for DelimitedParser.
    """
    def _createDefaultDialect(self):
        result = parsers.DelimitedDialect()
        result.lineDelimiter = parsers.LF
        result.itemDelimiter = ","
        result.quoteChar = "\""
        return result

    def _assertRowsEqual(self, expectedRows, readable, dialect=None):
        """
        Simply parse all items of `readable` using `dialect` and assert that the number of items read matches `expectedItem`.
        """
        assert expectedRows is not None
        assert readable is not None
        
        actualReadable = self.possiblyStringIoedReadable(readable)
        if dialect is None:
            actualDialect = self._createDefaultDialect()
        else:
            actualDialect = dialect
        reader = parsers.delimitedReader(actualReadable, actualDialect)
        self.readAndAssertEquals(expectedRows, reader)
        
    def _assertRaisesParserSyntaxError(self, readable, dialect=None):
        """
        Attempt to parse all items of `readable` using `dialect` and assert that this raises _`parsers.ParserSyntaxError`.
        """
        assert readable is not None
        
        actualReadable = self.possiblyStringIoedReadable(readable)
        if dialect is None:
            actualDialect = self._createDefaultDialect()
        else:
            actualDialect = dialect
        try:
            reader = parsers.delimitedReader(actualReadable, actualDialect)
            for dummy in reader:
                pass
            # FIXME: self.fail("readable must raise %s" % parsers.ParserSyntaxError.__name__)
        except parsers.ParserSyntaxError:
            # Ignore expected error.
            pass
        
    # TODO: Add test cases for linefeeds within quotes.
    # TODO: Add test cases for preservation of blanks between unquoted items.
       
    def testBrokenMissingQuote(self):
       self._assertRaisesParserSyntaxError("\"")
       
    def testSingleCharCsv(self):
        self._assertRowsEqual([["x"]], "x")

    def testQuotedCommaCsv(self):
        self._assertRowsEqual([["x", ",", "y"]], "x,\",\",y")

    def testItemDelimiterAtStartCsv(self):
        self._assertRowsEqual([["", "x"]], ",x")

    def testSingleItemDelimiterCsv(self):
        self._assertRowsEqual([["", ""]], ",")
        pass

    def testEmptyItemDelimiterBeforeLineDelimiterCsv(self):
        self._assertRowsEqual([["", ""], ["x"]], "," + parsers.LF + "x")

    def testSingleQuotedCharCsv(self):
        self._assertRowsEqual([["x"]], "\"x\"")

    def testSingleLineQuotedCsv(self):
        self._assertRowsEqual([["hugo", "was", "here"]], "\"hugo\",\"was\",\"here\"")

    def testSingleLineCsv(self):
        self._assertRowsEqual([["hugo", "was", "here"]], "hugo,was,here")

    def testTwoLineCsv(self):
        self._assertRowsEqual([["a"], ["b", "c"]], "a" + parsers.LF + "b,c")
        self._assertRowsEqual([["hugo", "was"], ["here", "again"]], "hugo,was" + parsers.LF + "here,again")

    def testMiddleEmptyLineCsv(self):
        self._assertRowsEqual([["a"], [], ["b", "c"]], "a" + parsers.LF + parsers.LF + "b,c")

    def testTwoLineQuotedCsv(self):
        self._assertRowsEqual([["hugo", "was"], ["here", "again"]], "\"hugo\",\"was\"" + parsers.LF + "\"here\",\"again\"")

    def testMixedQuotedLineCsv(self):
        self._assertRowsEqual([["hugo", "was", "here"]], "hugo,\"was\",here")
        
    def testEmptyCsv(self):
        self._assertRowsEqual([], "")
    
    def testAutoDelimiters(self):
        lineDelimiter = parsers.CRLF
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.AUTO
        dialect.itemDelimiter = parsers.AUTO
        self._assertRowsEqual([["a", "b"], ["c", "d", "e"]], "a,b" + parsers.CRLF + "c,d,e" + parsers.CRLF, dialect)
        
    def testEmptyLineWithLfCsv(self):
        self._assertRowsEqual([], parsers.LF)
    
    def testEmptyLineWithCrCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CR
        self._assertRowsEqual([], parsers.CR, dialect)
    
    def testEmptyLineWithCrLfCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CRLF
        self._assertRowsEqual([], parsers.CRLF, dialect)
        
    def testReader(self):
        dialect = self._createDefaultDialect()
        dataStream = StringIO.StringIO("hugo,was" + parsers.LF + "here,again")
        csvReader = parsers.delimitedReader(dataStream, dialect)
        rowCount = 0
        for row in csvReader:
            rowCount += 1
            self.assertEqual(2, len(row))
        self.assertEqual(2, rowCount)

    def testAutoItemDelimiter(self):
        dialect = self._createDefaultDialect()
        dialect.itemDelimiter = parsers.AUTO
        dataStream = StringIO.StringIO("some;items;using;a;semicolon;as;separator")
        csvReader = parsers.delimitedReader(dataStream, dialect)
        rowCount = 0
        for row in csvReader:
            rowCount += 1
            self.assertEqual(7, len(row))
        self.assertEqual(1, rowCount)
        
if __name__ == '__main__': # pragma: no cover
    logging.basicConfig()
    _log.setLevel(logging.DEBUG)
    unittest.main()
