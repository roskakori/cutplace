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

from cutplace import data
from cutplace import ranges


class DataFormatTest(unittest.TestCase):
    """
    Tests for data formats.
    """
    _TEST_ENCODING = "cp1252"

    def test_create_dataformat(self):
        for formatName in [data.FORMAT_DELIMITED, data.FORMAT_FIXED, data.FORMAT_EXCEL]:
            dataFormat = data.Dataformat(formatName)
            self.assertTrue(dataFormat)
            self.assertTrue(dataFormat.__str__())
        #self.assertRaises(data.DataFormatSyntaxError, data.createDataFormat, "no-such-data-format")

    def test_can_set_delimited_properties(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        delimited_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        delimited_format.set_property(data.KEY_HEADER, '0')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, ',')
        delimited_format.set_property(data.KEY_SPACE_AROUND_DELIMITER, 'True')
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, ',')
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, '\\')
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.CRLF)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '\"')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertTrue(delimited_format.validate)

    def test_can_set_fixed_properties(self):
        fixed_format = data.Dataformat(data.FORMAT_FIXED)
        fixed_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        fixed_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        fixed_format.set_property(data.KEY_HEADER, 0)
        fixed_format.set_property(data.KEY_DECIMAL_SEPARATOR, ',')
        fixed_format.set_property(data.KEY_ESCAPE_CHARACTER, '\\')
        fixed_format.set_property(data.KEY_LINE_DELIMITER, data.CRLF)
        fixed_format.set_property(data.KEY_QUOTE_CHARACTER, '\"')
        fixed_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertTrue(fixed_format.validate)

    def test_can_set_excel_properties(self):
        excel_format = data.Dataformat(data.FORMAT_EXCEL)
        excel_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        excel_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        excel_format.set_property(data.KEY_HEADER, 0)
        excel_format.set_property(data.KEY_SHEET, 1)
        self.assertTrue(excel_format.validate)

    def test_can_set_ods_properties(self):
        ods_format = data.Dataformat(data.FORMAT_ODS)
        ods_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        ods_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        ods_format.set_property(data.KEY_HEADER, 0)
        ods_format.set_property(data.KEY_SHEET, 1)
        self.assertTrue(ods_format.validate)

    def test_fails_on_unsupported_delimited_property(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        self.assertRaises(ValueError, delimited_format.set_property, data.KEY_SHEET, '2')

    def test_fails_on_unsupported_fixed_property(self):
        fixed_format = data.Dataformat(data.FORMAT_FIXED)
        self.assertRaises(ValueError, fixed_format.set_property, data.KEY_SHEET, 1)
        self.assertRaises(ValueError, fixed_format.set_property, data.KEY_ITEM_DELIMITER, ',')
        self.assertRaises(ValueError, fixed_format.set_property, data.KEY_SPACE_AROUND_DELIMITER, True)

    def test_fails_on_unsupported_excel_property(self):
        excel_format = data.Dataformat(data.FORMAT_EXCEL)
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_DECIMAL_SEPARATOR, ',')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_ESCAPE_CHARACTER, '\\')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_LINE_DELIMITER, '\n')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_QUOTE_CHARACTER, '"')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_ITEM_DELIMITER, ';')
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_SPACE_AROUND_DELIMITER, True)

    def test_fails_on_unsupported_ods_property(self):
        ods_format = data.Dataformat(data.FORMAT_ODS)
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_DECIMAL_SEPARATOR, ',')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_ESCAPE_CHARACTER, '\\')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_LINE_DELIMITER, '\n')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_QUOTE_CHARACTER, '"')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_ITEM_DELIMITER, ';')
        self.assertRaises(ValueError, ods_format.set_property, data.KEY_SPACE_AROUND_DELIMITER, True)

    def test_can_set_header(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_HEADER, '1')
        self.assertEqual(delimited_format.header, 1)

    def test_fails_on_nonnumeric_header(self):
        fixed_format = data.Dataformat(data.FORMAT_FIXED)
        self.assertRaises(ValueError, fixed_format.set_property, data.KEY_HEADER, 'xxx')

    def test_can_set_allowed_characters(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ALLOWED_CHARACTERS, '3...5')
        self.assertEqual([(3,5)], ranges.Range('3...5').items)

    def test_can_set_encoding(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        self.assertEqual(delimited_format.encoding, DataFormatTest._TEST_ENCODING)

    def test_fails_on_broken_encoding(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        self.assertRaises(ValueError, delimited_format.set_property, data.KEY_ENCODING, "broken-encoding")

    def test_can_set_item_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertEqual(delimited_format.item_delimiter, '.')

    def test_fails_on_broken_item_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, 'broken-item-delimiter')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_can_set_space_around_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_SPACE_AROUND_DELIMITER, 'True')
        self.assertEqual(delimited_format.space_around_delimiter, True)

    def test_can_set_decimal_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, '.')
        self.assertEqual(delimited_format.decimal_separator, '.')

    def test_fails_on_broken_decimal_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, 'broken-decimal-separator')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_can_set_escape_character(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, "\\")
        self.assertEqual(delimited_format.escape_character, '\\')

    def test_fails_on_broken_escape_character(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, 'broken-escape-character')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_can_set_line_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.CR)
        self.assertEqual(delimited_format.line_delimiter, '\r')

    def test_fails_on_unsupported_line_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        self.assertRaises(ValueError, delimited_format.set_property, data.KEY_LINE_DELIMITER, 'xx')

    def test_can_set_quote_character(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '"')
        self.assertEqual(delimited_format.quote_character, '"')

    def test_fails_on_broken_quote_character(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, 'broken-quote-character')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_can_set_thousands_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '')
        self.assertEqual(delimited_format.thousands_separator, '')

    def test_fails_on_broken_thousands_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, 'broken-thousands-separator')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_can_set_sheet(self):
        excel_format = data.Dataformat(data.FORMAT_EXCEL)
        excel_format.set_property(data.KEY_SHEET, '1')
        self.assertEqual(excel_format.sheet, 1)

    def test_fails_on_nonummeric_sheet(self):
        excel_format = data.Dataformat(data.FORMAT_EXCEL)
        self.assertRaises(ValueError, excel_format.set_property, data.KEY_SHEET, 'xxx')

    def test_fails_on_same_decimal_and_thousands_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, '.')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_fails_on_same_item_delimiter_and_thousands_separator(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_fails_on_same_quote_character_and_item_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '"')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '"')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_fails_on_same_line_and_item_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.LF)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '\n')
        self.assertRaises(ValueError, delimited_format.validate)

    def test_fails_on_same_escape_and_item_delimiter(self):
        delimited_format = data.Dataformat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, '\\')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '\\')
        self.assertRaises(ValueError, delimited_format.validate)


    """
    def testTransitionallySameDecimalSeparator(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        thousandsSeparator = dataFormat.decimal_separator(data.KEY_THOUSANDS_SEPARATOR)
        dataFormat.set_property(data.KEY_DECIMAL_SEPARATOR, thousandsSeparator)

    def testTransitionallySameThousandsSeparator(self):
        dataFormat = data.Dataformat(data.FORMAT_FIXED)
        decimalSeparator = dataFormat.thousands_separator(data.KEY_DECIMAL_SEPARATOR)
        dataFormat.set_property(data.KEY_THOUSANDS_SEPARATOR, decimalSeparator)
    """


    # TODO: implement errors
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

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
