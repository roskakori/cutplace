"""
Tests for parsers.
"""
import logging
import os
import parsers
import StringIO
import tools
import types
import unittest

_log = logging.getLogger("cutplace.parsers")

class CsvSyntaxError(tools.CutplaceError):
    pass

class CsvTokenizer(object):
    # Token types
    QUOTE = 1
    ITEM = 2
    ITEM_DELIMITER = 3
    LINE_DELIMITER = 4
    END_OF_DATA = 0
    
    # Tokenizer states.
    _AFTER_QUOTE_BEFORE_ITEM = 1
    _AFTER_ITEM = 2
    _AFTER_ITEM_DELIMITER = 3
    
    def __init__(self, readable, dialect):
        assert readable is not None
        assert dialect is not None
        self.readable = readable
        self.dialect = dialect
        self.state = CsvTokenizer._AFTER_ITEM_DELIMITER
        self.itemEndsWithQuote = False
        self.token = None
        self.nextToken = None
        self.lastRead = None
        self.lineNumber = 1
        self.columNumber = 1
        self._log = logging.getLogger("cutplace.parsers.CsvTokenizer")
        
        # Read first token
        self._read()
        self.advance()
        
    def _isAtEndOfLineMark(self, some):
        assert some is not None
        return (some == self.dialect.lineDelimiter) or ((self.dialect.lineDelimiter == parsers.AUTO) and some in ["\n", "\r", "\r\n"])
        
    def _read(self):
        self.lastRead = self.readable.read(1)
        if self.lastRead == "\r":
            charAfterCr = self.readable.read(1)
            if charAfterCr == "\n":
                self.lastRead += charAfterCr
            elif charAfterCr:
                self.readable.seek(-1, os.SEEK_CUR)
        if self._isAtEndOfLineMark(self.lastRead):
            # Advance line and reset column.
            self.lineNumber += 1
            self.columNumber = 1
        else:
            # Advance column.
            self.columNumber += len(self.lastRead)
        
    def _skipSpace(self):
        if self.lastRead and self.lastRead in self.dialect.blanksAroundItemDelimiter:
            self._log.debug("skip space: %r" % self.lastRead)
            self._read()
            
    def atEndOfData(self):
        return self.token[0] == CsvTokenizer.END_OF_DATA

    def advance(self):
        """
        Advance 1 token and update `token` accordingly.
        
        `self.token` is a tuple containing an (ID, data, (start line, start column), (end line, end column), `None`).
        Possible IDs are: `QUOTE,` `ITEM`, `ITEM_DELIMITER`, `LINE_DELIMITER` and `END_OF_DATA`.
        
        If `readable` does not contain any more data, `token` is ``(END_OF_DATA, None)``. Further
        attempts to call `advance()` will result in an `AssertionError`.
        """
        assert self.token == None or (self.token[0] != CsvTokenizer.END_OF_DATA)
        token = None
        startLocation = (self.lineNumber, self.columNumber)
        endLocation = None
        if self.nextToken is not None:
            token = self.nextToken
            self.nextToken = None
        elif self.lastRead == "":
            token = (CsvTokenizer.END_OF_DATA, None)
        elif self.state == CsvTokenizer._AFTER_QUOTE_BEFORE_ITEM:
            tokenText = ""
            while self.state == CsvTokenizer._AFTER_QUOTE_BEFORE_ITEM:
                if self.lastRead == "":
                    # Item ends because data end.
                    if self.itemEndsWithQuote:
                        raise CsvSyntaxError("quoted item must be closed with a quote (%r)" % dialect.quoteChar)
                    self.state = CsvTokenizer._AFTER_ITEM
                elif self.itemEndsWithQuote and (self.lastRead == self.dialect.quoteChar):
                    # Items ends because of quote.
                    self.state = CsvTokenizer._AFTER_ITEM
                    self.itemEndsWithQuote = False
                    self._read()
                elif not self.itemEndsWithQuote and (self.lastRead == self.dialect.itemDelimiter):
                    # Item ends because of delimiter.
                    self.state = CsvTokenizer._AFTER_ITEM
                else:
                    # Continue reading item.
                    tokenText += self.lastRead
                    self._read()
            if token is None:
                token = (CsvTokenizer.ITEM, tokenText)
            tokenText = None
        elif self.state == CsvTokenizer._AFTER_ITEM:
            self._skipSpace();
            if self.lastRead == "":
                token = (CsvTokenizer.END_OF_DATA, None)
            elif self.lastRead == self.dialect.itemDelimiter:
                self.state = CsvTokenizer._AFTER_ITEM_DELIMITER
                token = (CsvTokenizer.ITEM_DELIMITER, self.dialect.itemDelimiter)
                self._read()
            else:
                raise CsvSyntaxError("item delimiter (%r) or end of data expected" % (dialect.itemDelimiter))
        elif self.state == CsvTokenizer._AFTER_ITEM_DELIMITER:
            self._skipSpace()
            if not self.lastRead:
                token = (CsvTokenizer.END_OF_DATA, None)
            elif self.lastRead == self.dialect.quoteChar:
                self.state = CsvTokenizer._AFTER_QUOTE_BEFORE_ITEM
                token = (CsvTokenizer.QUOTE, self.lastRead)
                self.itemEndsWithQuote = True
                self._read()
            else:
                self.state = CsvTokenizer._AFTER_QUOTE_BEFORE_ITEM
                self.advance()
                token = (self.token[0], self.token[1])
                startLocation = self.token[2]
                endLocation = self.token[3]
        else:
            raise NotImplementedError("state=%r" % self.state)
        
        assert token is not None
        if endLocation is None:
            endLocation = (self.lineNumber, self.columNumber)
        self.token = (token[0], token[1], startLocation, endLocation, None)
        
class CsvTokenizerTest(unittest.TestCase):
    """
    TestCase for DelimitedParser.
    """
    def _createDefaultDialect(self):
        result = parsers.DelimitedDialect()
        result.lineDelimiter = parsers.LF
        result.itemDelimiter = ","
        result.quoteChar = "\""
        return result
    
    def _getIndexValue(self, index, values, defaults):
        assert index is not None
        assert values is not None
        assert defaults is not None
        assert index >= 0
        assert index < len(defaults)
        assert len(values) <= len(defaults)
        if index < len(values):
            result = values[index]
        else:
            result = defaults[index]
        return result
        
    def _testTokens(self, expected, data, dialect=None):
        assert expected is not None
        assert data is not None
        if dialect is None:
            dialect = self._createDefaultDialect()
        readable = StringIO.StringIO(data)
        toky = CsvTokenizer(readable, dialect)
        tokens = []
        expectedTokens = []
        expectedIndex = 0
        while not toky.atEndOfData():
            # TODO: Remove: print toky.token
            self.assertTrue(expectedIndex < len(expected), "token=%r, expectedIndex=%d, len(expected)=%d" %(toky.token, expectedIndex, len(expected)))
            tokens.append(toky.token)
            expectedItem = []
            for partIndex in range(0, len(toky.token)):
                expectedItem.append(self._getIndexValue(partIndex, expected[expectedIndex], toky.token))
            expectedIndex += 1
            expectedTokens.append(tuple(expectedItem))
            toky.advance()
        self.assertEqual(tokens, expectedTokens)
        
    def testEmpty(self):
        readable = StringIO.StringIO("")
        dialect = self._createDefaultDialect()
        toky = CsvTokenizer(readable, dialect)
        self.assertEqual((CsvTokenizer.END_OF_DATA, None, (1, 1), (1, 1), None), toky.token)

    def testSingleItem(self):
        self._testTokens([(CsvTokenizer.ITEM, "x")], "x")

    def testTwoItems(self):
        self._testTokens([
                          (CsvTokenizer.ITEM, "x"),
                          (CsvTokenizer.ITEM_DELIMITER, ","),
                          (CsvTokenizer.ITEM, "y")], "x,y")
	# FIXME: testQuotedItem
    def _testQuotedtem(self):
        self._testTokens([
                          (CsvTokenizer.ITEM, "x"),
                          (CsvTokenizer.ITEM_DELIMITER, ","),
                          (CsvTokenizer.ITEM, "y")], "\"x\",y")
        
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

    def parseAndAssertEquals(self, expectedRows, parser):
        rows = []
        for row in parsers.parserReader(parser):
            rows.append(row)
        self.assertEqual(rows, expectedRows)

class FixedParserTest(AbstractParserTest):
    _DEFAULT_FIELD_LENGTHS = [5, 4, 10]
        
    def _testParse(self, expectedRows, readable, fieldLengths=_DEFAULT_FIELD_LENGTHS):
        assert expectedRows is not None
        assert readable is not None
        assert fieldLengths is not None
        
        actualReadable = self.possiblyStringIoedReadable(readable)
        parser = parsers.FixedParser(actualReadable, fieldLengths)
        self.parseAndAssertEquals(expectedRows, parser)

    def testEmpty(self):
        self._testParse([], "")

    def testValid(self):
        self._testParse([["38000", " 123", "Doe       "]], "38000 123Doe       ")
        
    def testBrokenEndingTooSoon(self):
        self.assertRaises(parsers.ParserSyntaxError, self._testParse, [], "38000 123Doe  ")
    
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
        parser = parsers.DelimitedParser(actualReadable, actualDialect)
        self.parseAndAssertEquals(expectedRows, parser)
        
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
            parser = parsers.DelimitedParser(actualReadable, actualDialect)
            for dummy in parsers.parserReader(parser):
                pass
            self.fail("readable must raise %s" % parsers.ParserSyntaxError.__name__)
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
        # FIXME: self._assertRowsEqual([["", ""]], ",")
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
        self._assertRowsEqual([[""]], parsers.LF)
    
    def testEmptyLineWithCrCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CR
        self._assertRowsEqual([[""]], parsers.CR, dialect)
    
    def testEmptyLineWithCrLfCsv(self):
        dialect = self._createDefaultDialect()
        dialect.lineDelimiter = parsers.CRLF
        self._assertRowsEqual([[""]], parsers.CRLF, dialect)
        
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
