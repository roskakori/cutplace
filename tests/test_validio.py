"""
Tests for validator.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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

import io
import unittest

from cutplace import interface
from cutplace import errors
from cutplace import validio
from cutplace import rowio
from tests import dev_test


class ValidatorTest(unittest.TestCase):
    """
    Tests for data formats.
    """
    # TODO: Cleanup: rename all the ``cid_reader`` variables to ``cid``.
    _TEST_ENCODING = "cp1252"

    def test_can_open_and_validate_csv_source_file(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("valid_customers.csv"))
        reader.validate()

    def test_can_open_and_validate_excel_source_file(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers_excel.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("valid_customers.xls"))
        reader.validate()

    def test_can_open_and_validate_ods_source_file(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers_ods.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("valid_customers.ods"))
        reader.validate()

    def test_can_open_and_validate_fixed_source_file(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("customers_fixed.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("valid_customers_fixed.txt"))
        reader.validate()

    def test_fails_on_invalid_csv_source_file(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers.csv"))
        self.assertRaises(errors.FieldValueError, reader.validate)

    def test_fails_on_csv_source_file_with_fewer_elements_than_expected(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers_fewer_elements.csv"))
        self.assertRaises(errors.DataError, reader.validate)

    def test_fails_on_csv_source_file_with_more_elements_than_expected(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers_more_elements.csv"))
        self.assertRaises(errors.DataError, reader.validate)

    def test_fails_on_invalid_csv_source_file_with_duplicates(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers_with_duplicates.csv"))
        self.assertRaises(errors.CheckError, reader.validate)

    def test_fails_on_invalid_csv_source_file_with_not_observed_count_expression(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("icd_customers.xls")
        # FIXME: either test `validator` or move to `test_tools`.
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        reader = validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers_with_too_many_branches.csv"))
        self.assertRaises(errors.CheckError, reader.validate)

    def test_can_process_escape_character(self):
        """
        Regression test for #49: Fails when last char of field is escaped.
        """
        cid_text = '\n'.join([
            'd,format,delimited',
            'd,line delimiter,lf',
            'd,encoding,ascii',
            'd,quote character,""""',
            'd,escape character,"\\"',
            'f,some_fields'
        ])
        cid = interface.create_cid_from_string(cid_text)
        with io.StringIO('"\\"x"\n') as data_starting_with_escape_character:
            reader = validio.Reader(cid, data_starting_with_escape_character)
            reader.validate()
        with io.StringIO('"x\\""\n') as data_ending_with_escape_character:
            reader = validio.Reader(cid, data_ending_with_escape_character)
            reader.validate()

    def test_can_yield_errors(self):
        cid_text = '\n'.join([
            'd,format,delimited',
            'd,encoding,ascii',
            'f,some_number,,,,Integer'
        ])
        cid = interface.create_cid_from_string(cid_text)
        with io.StringIO('1\nabc\n3') as partially_broken_data:
            reader = validio.Reader(cid, partially_broken_data)
            rows = list(reader.rows('yield'))
        self.assertEqual(3, len(rows), 'expected 3 rows but got: %s' % rows)
        self.assertEqual(['1'], rows[0])
        self.assertEqual(errors.FieldValueError, type(rows[1]), 'rows=%s' % rows)
        self.assertEqual(['3'], rows[2])

    def test_can_continue_after_errors(self):
        cid_text = '\n'.join([
            'd,format,delimited',
            'd,encoding,ascii',
            'f,some_number,,,,Integer'
        ])
        cid = interface.create_cid_from_string(cid_text)
        with io.StringIO('1\nabc\n3') as partially_broken_data:
            reader = validio.Reader(cid, partially_broken_data)
            rows = list(reader.rows('continue'))
        self.assertEqual(2, len(rows), 'expected 3 rows but got: %s' % rows)
        self.assertEqual(['1'], rows[0])
        self.assertEqual(['3'], rows[1])
