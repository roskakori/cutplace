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
from cutplace import errors
from cutplace import ranges


class DataFormatTest(unittest.TestCase):

    """
    Tests for data formats.
    """
    _TEST_ENCODING = "cp1252"

    def test_create_data_format(self):
        for format_name in [data.FORMAT_DELIMITED, data.FORMAT_FIXED, data.FORMAT_EXCEL]:
            data_format = data.DataFormat(format_name)
            self.assertTrue(data_format)
            self.assertTrue(data_format.__str__())
        # self.assertRaises(data.InterfaceError, data.createDataFormat, "no-such-data-format")

    def test_fails_on_invalid_data_format(self):
        self.assertRaises(errors.InterfaceError, data.DataFormat, 'csv')

    def test_can_set_delimited_properties(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        delimited_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        delimited_format.set_property(data.KEY_HEADER, '0')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, ',')
        delimited_format.set_property(data.KEY_SKIP_INITIAL_SPACE, 'True')
        delimited_format.set_property(data.KEY_SKIP_INITIAL_SPACE, 'False')
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, ',')
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, '\\')
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.CRLF)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '\"')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertTrue(delimited_format.validate)

    def test_can_set_fixed_properties(self):
        fixed_format = data.DataFormat(data.FORMAT_FIXED)
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
        excel_format = data.DataFormat(data.FORMAT_EXCEL)
        excel_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        excel_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        excel_format.set_property(data.KEY_HEADER, 0)
        excel_format.set_property(data.KEY_SHEET, 1)
        self.assertTrue(excel_format.validate)

    def test_can_set_ods_properties(self):
        ods_format = data.DataFormat(data.FORMAT_ODS)
        ods_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        ods_format.set_property(data.KEY_ALLOWED_CHARACTERS, None)
        ods_format.set_property(data.KEY_HEADER, 0)
        ods_format.set_property(data.KEY_SHEET, 1)
        self.assertTrue(ods_format.validate)

    def test_fails_on_unsupported_delimited_property(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.InterfaceError, delimited_format.set_property, data.KEY_SHEET, '2')

    def test_fails_on_unsupported_fixed_property(self):
        fixed_format = data.DataFormat(data.FORMAT_FIXED)
        self.assertRaises(errors.InterfaceError, fixed_format.set_property, data.KEY_SHEET, 1)
        self.assertRaises(errors.InterfaceError, fixed_format.set_property, data.KEY_ITEM_DELIMITER, ',')
        self.assertRaises(errors.InterfaceError, fixed_format.set_property, data.KEY_SKIP_INITIAL_SPACE, True)

    def test_fails_on_unsupported_excel_property(self):
        excel_format = data.DataFormat(data.FORMAT_EXCEL)
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_DECIMAL_SEPARATOR, ',')
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_ESCAPE_CHARACTER, '\\')
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_LINE_DELIMITER, '\n')
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_QUOTE_CHARACTER, '"')
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_ITEM_DELIMITER, ';')
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_SKIP_INITIAL_SPACE, True)

    def test_fails_on_unsupported_ods_property(self):
        ods_format = data.DataFormat(data.FORMAT_ODS)
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_DECIMAL_SEPARATOR, ',')
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_ESCAPE_CHARACTER, '\\')
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_LINE_DELIMITER, '\n')
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_QUOTE_CHARACTER, '"')
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_ITEM_DELIMITER, ';')
        self.assertRaises(errors.InterfaceError, ods_format.set_property, data.KEY_SKIP_INITIAL_SPACE, True)

    def test_can_set_header(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_HEADER, '1')
        self.assertEqual(delimited_format.header, 1)

    def test_fails_on_non_numeric_header(self):
        fixed_format = data.DataFormat(data.FORMAT_FIXED)
        self.assertRaises(errors.InterfaceError, fixed_format.set_property, data.KEY_HEADER, 'xxx')

    def test_can_set_allowed_characters(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ALLOWED_CHARACTERS, '3...5')
        self.assertEqual([(3, 5)], ranges.Range('3...5').items)

    def test_fails_on_invalid_allowed_characters(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property, data.KEY_ALLOWED_CHARACTERS, '3..5')

    def test_can_set_encoding(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ENCODING, DataFormatTest._TEST_ENCODING)
        self.assertEqual(delimited_format.encoding, DataFormatTest._TEST_ENCODING)

    def test_fails_on_broken_encoding(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property, data.KEY_ENCODING, "broken-encoding")

    def test_can_set_item_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        self.assertEqual(delimited_format.item_delimiter, '.')

    def test_fails_on_broken_item_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.InterfaceError, delimited_format.set_property,
                          data.KEY_ITEM_DELIMITER, 'broken-item-delimiter')

    def test_can_set_skip_initial_space(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_SKIP_INITIAL_SPACE, 'True')
        self.assertEqual(delimited_format.skip_initial_space, True)

    def test_fails_on_invalid_skip_initial_space(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.InterfaceError, delimited_format.set_property, data.KEY_SKIP_INITIAL_SPACE, 'xx')

    def test_can_set_decimal_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, '.')
        self.assertEqual(delimited_format.decimal_separator, '.')

    def test_fails_on_broken_decimal_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property,
                          data.KEY_DECIMAL_SEPARATOR, 'broken-decimal-separator')

    def test_can_set_escape_character(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, "\\")
        self.assertEqual(delimited_format.escape_character, '\\')

    def test_fails_on_broken_escape_character(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property,
                          data.KEY_ESCAPE_CHARACTER, 'broken-escape-character')

    def test_can_set_line_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.CR)
        self.assertEqual(delimited_format.line_delimiter, '\r')

    def test_fails_on_unsupported_line_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property, data.KEY_LINE_DELIMITER, 'xx')

    def test_can_set_quote_character(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '"')
        self.assertEqual(delimited_format.quote_character, '"')

    def test_fails_on_broken_quote_character(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property,
                          data.KEY_QUOTE_CHARACTER, 'broken-quote-character')

    def test_can_set_thousands_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '')
        self.assertEqual(delimited_format.thousands_separator, '')

    def test_fails_on_broken_thousands_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        self.assertRaises(errors.DataFormatValueError, delimited_format.set_property,
                          data.KEY_THOUSANDS_SEPARATOR, 'broken-thousands-separator')

    def test_can_set_sheet(self):
        excel_format = data.DataFormat(data.FORMAT_EXCEL)
        excel_format.set_property(data.KEY_SHEET, '1')
        self.assertEqual(excel_format.sheet, 1)

    def test_fails_on_non_numeric_sheet(self):
        excel_format = data.DataFormat(data.FORMAT_EXCEL)
        self.assertRaises(errors.InterfaceError, excel_format.set_property, data.KEY_SHEET, 'xxx')

    def test_fails_on_same_decimal_and_thousands_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_DECIMAL_SEPARATOR, '.')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(errors.DataFormatValueError, delimited_format.validate)

    def test_fails_on_same_item_delimiter_and_thousands_separator(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '.')
        delimited_format.set_property(data.KEY_THOUSANDS_SEPARATOR, '.')
        self.assertRaises(errors.DataFormatValueError, delimited_format.validate)

    def test_fails_on_same_quote_character_and_item_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_QUOTE_CHARACTER, '"')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '"')
        self.assertRaises(errors.DataFormatValueError, delimited_format.validate)

    def test_fails_on_same_line_and_item_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_LINE_DELIMITER, data.LF)
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '\n')
        self.assertRaises(errors.DataFormatValueError, delimited_format.validate)

    def test_fails_on_same_escape_and_item_delimiter(self):
        delimited_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_format.set_property(data.KEY_ESCAPE_CHARACTER, '\\')
        delimited_format.set_property(data.KEY_ITEM_DELIMITER, '\\')
        self.assertRaises(errors.DataFormatValueError, delimited_format.validate)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_data").setLevel(logging.INFO)
    unittest.main()
