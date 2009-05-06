"""
Tests for data formats.
"""
import data
import logging
import unittest

class DataFormatTest(unittest.TestCase):
    """
    Tests for CsvDataFormat.
    """
    _TEST_ENCODING = "ascii"
    
    def testBasics(self):
        for formatName in [data.FORMAT_CSV, data.FORMAT_DELIMITED, data.FORMAT_FIXED]:
            format = data.createDataFormat(formatName)
            format.set(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
            self.assertEqual(format.getEncoding().name.lower(), DataFormatTest._TEST_ENCODING)
            format.set(data.KEY_LINE_DELIMITER, data.CR)
            self.assertEqual(format.getLineDelimiter(), "\r")
            format.set(data.KEY_ALLOWED_CHARACTERS, "32, 65...91")
            self.assertTrue(format.isAllowedCharacter("A"))
            # FIXME: self.assertFalse(format.isAllowedCharacter("?"))
            
    def testCsvDataFormat(self):
        format = data.CsvDataFormat()
        self.assertEqual(format.getLineDelimiter(), data.ANY)
        self.assertEqual(format.getItemDelimiter(), data.ANY)
        self.assertEqual(format.getQuoteCharacter(), "\"")
        self.assertEqual(format.getEscapeCharacter(), "\"")

        self.assertRaises(LookupError, format.setEncoding, "me-no-encoding")
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
