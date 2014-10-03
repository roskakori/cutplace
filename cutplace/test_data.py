"""
Tests for data formats.
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
import logging
import unittest

from . import data


class DataFormatTest(unittest.TestCase):
    """
    Tests for data formats.
    """
    _TEST_ENCODING = "iso-8859-1"

    def testCreateDataFormat(self):
        for formatName in [data.FORMAT_DELIMITED, data.FORMAT_FIXED, data.FORMAT_EXCEL]:
            dataFormat = data.Dataformat(formatName)
            self.assertTrue(dataFormat)
            self.assertTrue(dataFormat.__str__())
        #self.assertRaises(data.DataFormatSyntaxError, data.createDataFormat, "no-such-data-format")

    """
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
    """

    def testDelimitedDataFormat(self):
        dataFormat = data.Dataformat(data.FORMAT_DELIMITED)
        self.assertTrue(dataFormat.format)
        #self.assertRaises(data.DataFormatSyntaxError, dataFormat.validateAllRequiredPropertiesHaveBeenSet)

        formatWithCr = data.Dataformat(data.FORMAT_DELIMITED)
        formatWithCr.set_property(data.KEY_LINE_DELIMITER, data.CR)
        self.assertEqual(formatWithCr.line_delimiter, "\r")

    def test_excel_format(self):
        data_format = data.Dataformat()
        self.assertRaises(ValueError, data_format.validate(), None, "format must be specified")
        data_format.set_property(data.KEY_FORMAT,data.FORMAT_EXCEL)
        data_format.set_property(data.KEY_SHEET, '1')
        self.assertEqual('1',data_format.sheet)
        self.assertTrue(data_format.validate())
        data_format = data.Dataformat(data.FORMAT_EXCEL)
        self.assertRaises(data_format.validate())

    # TODO implement ODS format
    """
    def testOdsDataFormat(self):
        dataFormat = data.OdsDataFormat()
        self.assertTrue(dataFormat.name)
        dataFormat.validateAllRequiredPropertiesHaveBeenSet()
        dataFormat.set(data.KEY_ALLOWED_CHARACTERS, "32:")
        self.assertRaises(data.DataFormatSyntaxError, dataFormat.set, data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
    """

    def testHeader(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        dataFormat.set_property(data.KEY_HEADER, 17)
        newHeader = dataFormat.header
        self.assertEquals(17, newHeader)

    def testDecimalAndThousandsSeparator(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        self.assertEquals(".", dataFormat.thousands_separator(data.KEY_DECIMAL_SEPARATOR))
        self.assertEquals(",", dataFormat.thousands_separator(data.KEY_THOUSANDS_SEPARATOR))
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        dataFormat.set_property(data.KEY_DECIMAL_SEPARATOR, ",")
        self.assertEquals(",", dataFormat.thousands_separator(data.KEY_DECIMAL_SEPARATOR))
        dataFormat.set_property(data.KEY_THOUSANDS_SEPARATOR, ".")
        self.assertEquals(".", dataFormat.thousands_separator(data.KEY_THOUSANDS_SEPARATOR))

    def testTransitionallySameDecimalSeparator(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        thousandsSeparator = dataFormat.decimal_separator(data.KEY_THOUSANDS_SEPARATOR)
        dataFormat.set_property(data.KEY_DECIMAL_SEPARATOR, thousandsSeparator)

    def testTransitionallySameThousandsSeparator(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        decimalSeparator = dataFormat.thousands_separator(data.KEY_DECIMAL_SEPARATOR)
        dataFormat.set_property(data.KEY_THOUSANDS_SEPARATOR, decimalSeparator)

    # TODO implement errors
    """
    def testBrokenEncoding(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
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
    """

    def test_validate(self):
        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_DECIMAL_SEPARATOR,'.')
        data_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_QUOTE_CHARACTER,'.')
        data_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_QUOTE_CHARACTER,'.')
        data_format.set_property(data.KEY_DECIMAL_SEPARATOR, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_ITEM_DELIMITER,'.')
        data_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_DECIMAL_SEPARATOR,'.')
        data_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_SPACE_AROUND_DELIMITER,'.')
        data_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_QUOTE_CHARACTER,'.')
        data_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_LINE_DELIMITER,'.')
        data_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_ITEM_DELIMITER,'.')
        data_format.set_property(data.KEY_ESCAPE_CHARACTER, '.')
        self.assertRaises(ValueError,data_format.validate())

        data_format = data.Dataformat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_ALLOWED_CHARACTERS,'.')
        data_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertRaises(ValueError,data_format.validate())

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
