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
import os

import logging
import unittest


class Cidtest(unittest.TestCase):
    """
    Tests for cid module
    """
    _TEST_ENCODING = "cp1252"

    def test_can_read_excel_and_create_dataformat_delimited(self):
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
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read,'inline', [
            ['d', 'format', 'delimited'],
            ['d', 'header'],
        ])

    def test_fails_on_missing_data_format_property_name(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read,'inline', [
            ['d', 'format', 'delimited'],
            ['d'],
        ])

    def test_fails_on_invalid_row_typ(self):
        cid_reader = cid.Cid()
        self.assertRaises(errors.DataFormatSyntaxError, cid_reader.read,'inline',[['x']])

    def test_can_skip_empty_rows(self):
        cid_reader = cid.Cid()
        cid_reader.read('inline',[
            [],
            ['d','format','delimited']])
        self.assertEqual(cid_reader._data_format.format, "delimited")

