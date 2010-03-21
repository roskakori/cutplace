"""
Tests for data formats.
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
            self.assertTrue(format.__str__())
        self.assertRaises(data.DataFormatSyntaxError, data.createDataFormat, "no-such-format")
            
    def testCsvDataFormat(self):
        format = data.CsvDataFormat()
        self.assertTrue(format.name)
        self.assertEqual(format.encoding, "ascii")

        format.encoding = DataFormatTest._TEST_ENCODING
        self.assertEqual(format.encoding, DataFormatTest._TEST_ENCODING)

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
        self.assertRaises(data.DataFormatValueError, format.set, data.KEY_ENCODING, "broken-encoding")
        
    def testBrokenLineDelimiter(self):
        format = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, format.set, data.KEY_LINE_DELIMITER, "broken-line-delimiter")
        
    def testBrokenEscapeCharacter(self):
        format = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, format.set, data.KEY_ESCAPE_CHARACTER, "broken-escape-character")
        
    def testBrokenQuoteCharacter(self):
        format = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, format.set, data.KEY_QUOTE_CHARACTER, "broken-quote-character")
        
    def testBrokenPropertyName(self):
        format = data.CsvDataFormat()
        self.assertRaises(data.DataFormatSyntaxError, format.set, "broken-property-name", "")
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
