"""Tests for parsers"""
import logging
import parsers
import StringIO
import types
import unittest

_log = logging.getLogger("cutplace.parsers")

class DelimiterParserTest(unittest.TestCase):
    """TestCase for DelimiterParser."""
    
    def _assertItemsEqual(self, expectedItems, readable, dialect):
        """Simply parse all items of readable using dialect and assert that the number of items read matches expectedItemCount."""
        assert expectedItems is not None
        assert readable is not None
        assert dialect is not None
        
        if isinstance(readable, types.StringTypes):
            actualReadable = StringIO.StringIO(readable)
        else:
            actualReadable = readable
        parser = parsers.DelimitedParser(actualReadable, dialect)
        rows = []
        columns = []
        while not parser.atEndOfFile:
            _log.debug("eof=" + str(parser.atEndOfFile) + ",eol=" + str(parser.atEndOfLine))
            columns.append(parser.item)
            if parser.atEndOfLine:
                rows.append(columns)
                columns = []
            parser.advance()
        self.assertEqual(rows, expectedItems)
        
    def testSingleCharCsv(self):
        dialect = parsers.DelimitedDialect(itemDelimiter=",")
        self._assertItemsEqual([["x"]], "x", dialect)

    def testSingleLineCsv(self):
        dialect = parsers.DelimitedDialect(itemDelimiter=",")
        self._assertItemsEqual([["hugo", "was", "here"]], "hugo,was,here", dialect)

    def testMixedQuotedLineCsv(self):
        dialect = parsers.DelimitedDialect(itemDelimiter=",")
        dialect.quoteChar = "\""
        self._assertItemsEqual([["hugo", "was", "here"]], "hugo,\"was\",here", dialect)
        
    def testEmptyCsv(self):
        dialect = parsers.DelimitedDialect(itemDelimiter=",")
        self._assertItemsEqual([], "", dialect)
    
if __name__ == '__main__':
    logging.basicConfig()
    log.setLevel(logging.INFO)
    unittest.main()
