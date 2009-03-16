"""Tests for parsers"""
import logging
import parsers
import StringIO
import types
import unittest

_log = logging.getLogger("cutplace.parsers")

class DelimitedParserTest(unittest.TestCase):
    """TestCase for DelimiterParser."""
    
    def _createDefaultDialect(self):
        result = parsers.DelimitedDialect()
        result.lineDelimiter = parsers.LF
        result.itemDelimiter = ","
        result.quoteChar = "\""
        return result

    def _assertItemsEqual(self, expectedItems, readable, dialect=None):
        """Simply parse all items of readable using dialect and assert that the number of items read matches expectedItemCount."""
        assert expectedItems is not None
        assert readable is not None
        
        if isinstance(readable, types.StringTypes):
            actualReadable = StringIO.StringIO(readable)
        else:
            actualReadable = readable
        if dialect is None:
            actualDialect = self._createDefaultDialect()
        else:
            actualDialect = dialect
        parser = parsers.DelimitedParser(actualReadable, actualDialect)
        rows = []
        for row in parsers.parserReader(parser):
            rows.append(row)
        self.assertEqual(rows, expectedItems)
        
    # TODO: Add test cases for linefeeds within quotes.
    # TODO: Add test cases for preservation of blanks between unquoted items.
       
    def testSingleCharCsv(self):
        self._assertItemsEqual([["x"]], "x")

    def testQuotedCommaCsv(self):
        self._assertItemsEqual([["x", ",", "y"]], "x,\",\",y")

    def testItemDelimiterAtStartCsv(self):
        self._assertItemsEqual([["", "x"]], ",x")

    def testSingleItemDelimiterCsv(self):
        # FIXME: self._assertItemsEqual([["", ""]], ",")
        pass

    def testEmptyItemDelimiterBeforeLineDelimiterCsv(self):
        self._assertItemsEqual([["", ""], ["x"]], "," + parsers.LF + "x")

    def testSingleQuotedCharCsv(self):
        self._assertItemsEqual([["x"]], "\"x\"")

    def testSingleLineQuotedCsv(self):
        self._assertItemsEqual([["hugo", "was", "here"]], "\"hugo\",\"was\",\"here\"")

    def testSingleLineCsv(self):
        self._assertItemsEqual([["hugo", "was", "here"]], "hugo,was,here")

    def testTwoLineCsv(self):
        self._assertItemsEqual([["a"], ["b", "c"]], "a" + parsers.LF + "b,c")
        self._assertItemsEqual([["hugo", "was"], ["here", "again"]], "hugo,was" + parsers.LF + "here,again")

    def testTwoLineQuotedCsv(self):
        self._assertItemsEqual([["hugo", "was"], ["here", "again"]], "\"hugo\",\"was\"" + parsers.LF + "\"here\",\"again\"")

    def testMixedQuotedLineCsv(self):
        self._assertItemsEqual([["hugo", "was", "here"]], "hugo,\"was\",here")
        
    def testEmptyCsv(self):
        self._assertItemsEqual([], "")
    
    def testAutoDelimiters(self):
        lineDelimiter = parsers.CRLF
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.AUTO
        dialect.itemDelimiter = parsers.AUTO
        self._assertItemsEqual([["a", "b"], ["c", "d", "e"]], "a,b" + parsers.CRLF + "c,d,e" + parsers.CRLF, dialect)
        
    def testEmptyLineWithLfCsv(self):
        self._assertItemsEqual([[""]], parsers.LF)
    
    def testEmptyLineWithCrCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CR
        self._assertItemsEqual([[""]], parsers.CR, dialect)
    
    def testEmptyLineWithCrLfCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CRLF
        self._assertItemsEqual([[""]], parsers.CRLF, dialect)
        
    def testReader(self):
        dialect = self._createDefaultDialect()
        dataStream = StringIO.StringIO("hugo,was" + parsers.LF + "here,again")
        csvReader = parsers.delimitedReader(dataStream, dialect)
        rowCount = 0
        for row in csvReader:
            rowCount += 1
            self.assertEqual(2, len(row))
        self.assertEqual(2, rowCount)
    
if __name__ == '__main__':
    logging.basicConfig()
    _log.setLevel(logging.INFO)
    unittest.main()
