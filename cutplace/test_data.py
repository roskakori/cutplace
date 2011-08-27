"""
Tests for data formats.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
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
import logging
import unittest

import data


class DataFormatTest(unittest.TestCase):
    """
    Tests for data formats.
    """
    _TEST_ENCODING = "iso-8859-1"

    def testCreateDataFormat(self):
        for formatName in [data.FORMAT_CSV, data.FORMAT_DELIMITED, data.FORMAT_FIXED, data.FORMAT_ODS]:
            dataFormat = data.createDataFormat(formatName)
            self.assertTrue(dataFormat)
            self.assertTrue(dataFormat.__str__())
        self.assertRaises(data.DataFormatSyntaxError, data.createDataFormat, "no-such-data-format")

    def testCsvDataFormat(self):
        dataFormat = data.CsvDataFormat()
        self.assertTrue(dataFormat.name)
        self.assertEqual(dataFormat.encoding, "ascii")

        dataFormat.encoding = DataFormatTest._TEST_ENCODING
        self.assertEqual(dataFormat.encoding, DataFormatTest._TEST_ENCODING)

        self.assertEqual(dataFormat.get(data.KEY_LINE_DELIMITER), data.ANY)
        self.assertEqual(dataFormat.get(data.KEY_ITEM_DELIMITER), data.ANY)
        self.assertEqual(dataFormat.get(data.KEY_QUOTE_CHARACTER), "\"")
        self.assertEqual(dataFormat.get(data.KEY_ESCAPE_CHARACTER), "\"")
        dataFormat.validateAllRequiredPropertiesHaveBeenSet()

    def testDelimitedDataFormat(self):
        dataFormat = data.DelimitedDataFormat()
        self.assertTrue(dataFormat.name)
        self.assertRaises(data.DataFormatSyntaxError, dataFormat.validateAllRequiredPropertiesHaveBeenSet)

        formatWithCr = data.DelimitedDataFormat()
        formatWithCr.set(data.KEY_LINE_DELIMITER, data.CR)
        self.assertEqual(formatWithCr.get(data.KEY_LINE_DELIMITER), "\r")

    def testOdsDataFormat(self):
        dataFormat = data.OdsDataFormat()
        self.assertTrue(dataFormat.name)
        dataFormat.validateAllRequiredPropertiesHaveBeenSet()
        dataFormat.set(data.KEY_ALLOWED_CHARACTERS, "32:")
        self.assertRaises(data.DataFormatSyntaxError, dataFormat.set, data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)

    def testHeader(self):
        dataFormat = data.CsvDataFormat()
        self.assertEquals(0, dataFormat.get(data.KEY_HEADER))
        dataFormat.set(data.KEY_HEADER, 17)
        newHeader = dataFormat.get(data.KEY_HEADER)
        self.assertEquals(17, newHeader)

    def testDecimalAndThousandsSeparator(self):
        dataFormat = data.CsvDataFormat()
        self.assertEquals(".", dataFormat.get(data.KEY_DECIMAL_SEPARATOR))
        self.assertEquals(",", dataFormat.get(data.KEY_THOUSANDS_SEPARATOR))
        dataFormat.set(data.KEY_DECIMAL_SEPARATOR, ",")
        self.assertEquals(",", dataFormat.get(data.KEY_DECIMAL_SEPARATOR))
        dataFormat.set(data.KEY_THOUSANDS_SEPARATOR, ".")
        self.assertEquals(".", dataFormat.get(data.KEY_THOUSANDS_SEPARATOR))

    def testTransitionallySameDecimalSeparator(self):
        dataFormat = data.CsvDataFormat()
        thousandsSeparator = dataFormat.get(data.KEY_THOUSANDS_SEPARATOR)
        dataFormat.set(data.KEY_DECIMAL_SEPARATOR, thousandsSeparator)

    def testTransitionallySameThousandsSeparator(self):
        dataFormat = data.CsvDataFormat()
        decimalSeparator = dataFormat.get(data.KEY_DECIMAL_SEPARATOR)
        dataFormat.set(data.KEY_THOUSANDS_SEPARATOR, decimalSeparator)

    def testBrokenEncoding(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_ENCODING, "broken-encoding")

    def testBrokenLineDelimiter(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_LINE_DELIMITER, "broken-line-delimiter")

    def testBrokenEscapeCharacter(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_ESCAPE_CHARACTER, "broken-escape-character")

    def testBrokenQuoteCharacter(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_QUOTE_CHARACTER, "broken-quote-character")

    def testBrokenDecimalSeparator(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_DECIMAL_SEPARATOR, "broken-decimal-separator")

        # Attempt to set decimal separator to the same value as thousands separator.
        thousandsSeparator = dataFormat.get(data.KEY_THOUSANDS_SEPARATOR)
        dataFormat.set(data.KEY_THOUSANDS_SEPARATOR, thousandsSeparator)
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_DECIMAL_SEPARATOR, thousandsSeparator)

    def testBrokenThousandsSeparator(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_THOUSANDS_SEPARATOR, "broken-thousands-separator")

        # Attempt to set thousands separator to the same value as decimal separator.
        decimalSeparator = dataFormat.get(data.KEY_DECIMAL_SEPARATOR)
        dataFormat.set(data.KEY_DECIMAL_SEPARATOR, decimalSeparator)
        self.assertRaises(data.DataFormatValueError, dataFormat.set, data.KEY_THOUSANDS_SEPARATOR, decimalSeparator)

    def testBrokenPropertyName(self):
        dataFormat = data.CsvDataFormat()
        self.assertRaises(data.DataFormatSyntaxError, dataFormat.set, "broken-property-name", "")


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
