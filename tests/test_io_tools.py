"""
Test for `_io_tools` module.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from cutplace import interface
from cutplace import errors
from cutplace import iotools
from tests import dev_test


class RowsTest(unittest.TestCase):
    def _assert_rows_contain_data(self, rows):
        self.assertTrue(rows is not None)

        # Convert possible generator to list so it can be queried multiple times.
        rows_as_list = list(rows)

        self.assertTrue(len(rows_as_list) > 0)
        none_empty_rows = [row for row in rows_as_list if len(row) > 0]
        self.assertTrue(len(none_empty_rows) > 0)

    def test_can_read_excel_rows(self):
        excel_path = dev_test.path_to_test_data('valid_customers.xls')
        self._assert_rows_contain_data(iotools.excel_rows(excel_path))

    def test_can_read_ods_rows(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        self._assert_rows_contain_data(iotools.ods_rows(ods_path))

    def test_fails_on_ods_with_broken_zip(self):
        broken_ods_path = dev_test.path_to_test_data('customers.csv')
        try:
            list(iotools.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue('cannot uncompress ODS spreadsheet:' in error_message,
                    'error_message=%r' % error_message)

    def test_fails_on_ods_without_content_xml(self):
        broken_ods_path = dev_test.path_to_test_data('broken_without_content_xml.ods')
        try:
            list(iotools.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue('cannot extract content.xml' in error_message,
                    'error_message=%r' % error_message)

    def test_fails_on_ods_without_broken_content_xml(self):
        broken_ods_path = dev_test.path_to_test_data('broken_content_xml.ods')
        try:
            list(iotools.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue('cannot parse content.xml' in error_message,
                    'error_message=%r' % error_message)

    def test_fails_on_non_existent_ods_sheet(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        try:
            list(iotools.ods_rows(ods_path, 123))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue('ODS must contain at least' in error_message,
                    'error_message=%r' % error_message)

    def test_fails_on_delimited_with_unterminated_quote(self):
        cid_path = dev_test.path_to_test_cid('customers.ods')
        customer_cid = interface.Cid(cid_path)
        broken_delimited_path = dev_test.path_to_test_data('broken_customers_with_unterminated_quote.csv')
        try:
            list(iotools.delimited_rows(broken_delimited_path, customer_cid.data_format))
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue('cannot parse delimited file' in error_message,
                    'error_message=%r' % error_message)

    def test_can_read_fixed_rows(self):
        cid_path = dev_test.path_to_test_cid('customers_fixed.ods')
        customer_cid = interface.Cid(cid_path)
        fixed_path = dev_test.path_to_test_data('valid_customers_fixed.txt')
        field_names_and_lengths = interface.field_names_and_lengths(customer_cid)
        rows = list(iotools.fixed_rows(fixed_path, customer_cid.data_format.encoding, field_names_and_lengths))
        self.assertNotEqual(0, len(rows))
        for row_index in range(len(rows) - 1):
            row = rows[row_index]
            next_row = rows[row_index + 1]
            self.assertNotEqual(0, len(row))
            self.assertEqual(len(row), len(next_row))

    def test_can_auto_read_excel_rows(self):
        excel_path = dev_test.path_to_test_data('valid_customers.xls')
        self._assert_rows_contain_data(iotools.auto_rows(excel_path))

    def test_can_auto_read_ods_rows(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        self._assert_rows_contain_data(iotools.auto_rows(ods_path))



if __name__ == "__main__":  # pragma: no cover
    unittest.main()
