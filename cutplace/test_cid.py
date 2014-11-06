"""
Tests for `cid` module
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
#

from cutplace import cid
from cutplace import dev_test
from cutplace import _tools
from cutplace import errors
from cutplace import ranges
from cutplace import data

import unittest


class CidTest(unittest.TestCase):

    """
    Tests for cid module
    """
    _TEST_ENCODING = "cp1252"

    def test_can_read_excel_and_create_data_format_delimited(self):
        cid_reader = cid.Cid()
        source_path = dev_test.getTestIcdPath("icd_customers.xls")
        print(source_path)
        cid_reader.read(source_path, _tools.excel_rows(source_path))

        self.assertEqual(cid_reader._data_format.format, "delimited")
        self.assertEqual(cid_reader._data_format.header, 1)

    def test_fails_on_empty_data_format_property_name(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d', '', ''],
        ])

    def test_fails_on_missing_data_format_value_name(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d', 'header'],
        ])

    def test_fails_on_missing_data_format_property_name(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d'],
        ])

    def test_fails_on_invalid_row_typ(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read, 'inline', [['x']])

    def test_can_skip_empty_rows(self):
        cid_reader = cid.Cid()
        cid_reader.read('inline', [
            [],
            [''],
            ['d', 'format', 'delimited']])
        self.assertEqual(cid_reader._data_format.format, "delimited")

    def test_can_read_field_type_text_field(self):
        cid_reader = cid.Cid()
        cid_reader.read('inline', [
            ['d', 'format', 'delimited'],
            ['f', 'branch_id', '38000', '', '5']])
        self.assertEqual(cid_reader._fields[0].fieldName, 'branch_id')
        self.assertEqual(cid_reader._fields[0].length.description, ranges.Range('5').description)

    def test_can_read_fields_from_excel(self):
        cid_reader = cid.Cid()
        source_path = dev_test.getTestIcdPath("icd_customers.xls")
        cid_reader.read(source_path, _tools.excel_rows(source_path))
        self.assertEqual(cid_reader._fields[0].fieldName, 'branch_id')
        self.assertEqual(cid_reader._fields[0].length.items, ranges.Range('5').items)
        self.assertEqual(cid_reader._fields[1].fieldName, 'customer_id')
        self.assertEqual(cid_reader._fields[1].length.items, ranges.Range('2...').items)
        self.assertEqual(cid_reader._fields[2].fieldName, 'first_name')
        self.assertEqual(cid_reader._fields[2].length.items, ranges.Range('...60').items)
        self.assertEqual(cid_reader._fields[3].fieldName, 'surname')
        self.assertEqual(cid_reader._fields[3].length.items, ranges.Range('...60').items)
        self.assertEqual(cid_reader._fields[4].fieldName, 'gender')
        self.assertEqual(cid_reader._fields[4].length.items, ranges.Range('2...6').items)
        self.assertEqual(cid_reader._fields[5].fieldName, 'date_of_birth')
        self.assertTrue(cid_reader._fields[5].isAllowedToBeEmpty)
        self.assertEqual(cid_reader._fields[5].length.items, ranges.Range('10').items)

    def test_fails_on_empty_field_name(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.FieldSyntaxError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['f', '', '38000', '', '5']])

    def test_can_read_delimited_rows(self):
        cid_reader = cid.Cid()
        source_path = dev_test.getTestIcdPath("icd_customers.xls")

        cid_reader.read(source_path, _tools.excel_rows(source_path))

        data_format = cid_reader._data_format
        data_format.set_property(data.KEY_LINE_DELIMITER, data.CRLF)
        data_format.set_property(data.KEY_ESCAPE_CHARACTER, "\\")

        delimited_rows = _tools.delimited_rows(dev_test.getTestInputPath("valid_customers.csv"), cid_reader._data_format)

        for row in delimited_rows:
            delimited_row = row
            break

        self.assertEqual(delimited_row, ['38000', '23', 'John', 'Doe', 'male', '08.03.1957'])


if __name__ == '__main__':
    unittest.main()
