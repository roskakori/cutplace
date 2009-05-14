"""
Tests for data formats.
"""
import codecs
import data
import logging
import unittest

class DataFormatTest(unittest.TestCase):
    """
    Tests for data formats.
    """
    _TEST_ENCODING = "iso-8859-1"

    def testCreateDataFormat(self):
        for formatName in [data.FORMAT_CSV, data.FORMAT_DELIMITED, data.FORMAT_FIXED, data.FORMAT_ODS]:
            format = data.createDataFormat(formatName)
            self.assertTrue(format)
        self.assertRaises(data.DataFormatSyntaxError, data.createDataFormat, "no-such-format")
            
    def testCsvDataFormat(self):
        format = data.CsvDataFormat()
        self.assertTrue(format.name)
        self.assertEqual(format.get(data.KEY_ENCODING), codecs.lookup("ascii"))

        format.set(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        self.assertEqual(format.get(data.KEY_ENCODING), codecs.lookup(DataFormatTest._TEST_ENCODING))

        self.assertEqual(format.get(data.KEY_LINE_DELIMITER), data.ANY)
        self.assertEqual(format.get(data.KEY_ITEM_DELIMITER), data.ANY)
        self.assertEqual(format.get(data.KEY_QUOTE_CHARACTER), "\"")
        self.assertEqual(format.get(data.KEY_ESCAPE_CHARACTER), "\"")
        format.validateAllRequiredPropertiesHaveBeenSet()
        
    def testDelimitedDataFormat(self):
        format = data.DelimitedDataFormat()
        self.assertTrue(format.name)
        self.assertRaises(data.DataFormatSyntaxError, format.validateAllRequiredPropertiesHaveBeenSet)

        formatWithCr = data.DelimitedDataFormat()
        formatWithCr.set(data.KEY_LINE_DELIMITER, data.CR)
        self.assertEqual(formatWithCr.get(data.KEY_LINE_DELIMITER), "\r")
        
    def testOdsDataFormat(self):
        format = data.OdsDataFormat()
        self.assertTrue(format.name)
        format.validateAllRequiredPropertiesHaveBeenSet()
        format.set(data.KEY_ALLOWED_CHARACTERS, "32:")
        self.assertRaises(data.DataFormatSyntaxError, format.set, data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        
    def testHeader(self):
        format = data.CsvDataFormat()
        self.assertEquals(0, format.get(data.KEY_HEADER))
        format.set(data.KEY_HEADER, 17)
        newHeader = format.get(data.KEY_HEADER)
        self.assertEquals(17, newHeader)
                          
    def testBrokenEncoding(self):
        format = data.CsvDataFormat()
        self.assertRaises(data.DataFormatSyntaxError, format.set, data.KEY_ENCODING, "me-no-encoding")
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
