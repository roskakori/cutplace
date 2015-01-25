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

_TEST_ENCODING = "cp1252"


class ReaderTest(unittest.TestCase):
    """
    Tests for data formats.
    """

    def test_can_open_and_validate_csv_source_file(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("valid_customers.csv")) as reader:
            reader.validate_rows()

    def test_can_open_and_validate_excel_source_file(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers_excel.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("valid_customers.xls")) as reader:
            reader.validate_rows()

    def test_can_open_and_validate_ods_source_file(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers_ods.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("valid_customers.ods")) as reader:
            reader.validate_rows()

    def test_can_open_and_validate_fixed_source_file(self):
        cid = interface.Cid(dev_test.path_to_test_cid("customers_fixed.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("valid_customers_fixed.txt")) as reader:
            reader.validate_rows()

    def test_fails_on_invalid_csv_source_file(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("broken_customers.csv")) as reader:
            self.assertRaises(errors.FieldValueError, reader.validate_rows)

    def test_fails_on_csv_source_file_with_fewer_elements_than_expected(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("broken_customers_fewer_elements.csv")) as reader:
            self.assertRaises(errors.DataError, reader.validate_rows)

    def test_fails_on_csv_source_file_with_more_elements_than_expected(self):
        cid_reader = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        with validio.Reader(cid_reader, dev_test.path_to_test_data("broken_customers_more_elements.csv")) as reader:
            self.assertRaises(errors.DataError, reader.validate_rows)

    def test_fails_on_invalid_csv_source_file_with_duplicates(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        with validio.Reader(cid, dev_test.path_to_test_data("broken_customers_with_duplicates.csv")) as  reader:
            self.assertRaises(errors.CheckError, reader.validate_rows)

    def test_fails_on_invalid_csv_source_file_with_not_observed_count_expression(self):
        cid = interface.Cid(dev_test.path_to_test_cid("icd_customers.xls"))
        data_path = dev_test.path_to_test_data("broken_customers_with_too_many_branches.csv")
        reader = validio.Reader(cid, data_path)
        reader.validate_rows()
        self.assertRaises(errors.CheckError, reader.close)

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
            with validio.Reader(cid, data_starting_with_escape_character) as reader:
                reader.validate_rows()
        with io.StringIO('"x\\""\n') as data_ending_with_escape_character:
            with validio.Reader(cid, data_ending_with_escape_character) as reader:
                reader.validate_rows()

    def test_can_yield_errors(self):
        cid_text = '\n'.join([
            'd,format,delimited',
            'd,encoding,ascii',
            'f,some_number,,,,Integer'
        ])
        cid = interface.create_cid_from_string(cid_text)
        with io.StringIO('1\nabc\n3') as partially_broken_data:
            with validio.Reader(cid, partially_broken_data) as reader:
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
            with validio.Reader(cid, partially_broken_data) as reader:
                rows = list(reader.rows('continue'))
        expected_row_count = 2
        self.assertEqual(expected_row_count, len(rows), 'expected %d rows but got: %s' % (expected_row_count, rows))
        self.assertEqual([['1'], ['3']], rows)


class WriterTest(unittest.TestCase):
    def setUp(self):
        standard_cid_text = '\n'.join([
            'd,format,delimited',
            ' ,name   ,,empty,length,type,rule',
            'f,surname',
            'f,height ,,     ,      ,Integer',
            'f,born_on,,     ,      ,DateTime,YYYY-MM-DD'
        ])
        self._standard_cid = interface.create_cid_from_string(standard_cid_text)

    def test_can_write_delimited(self):
        with io.StringIO() as delimited_stream:
            with validio.Writer(self._standard_cid, delimited_stream) as delimited_writer:
                delimited_writer.write_row(['Miller', '173', '1967-05-23'])
                delimited_writer.write_row(['Webster', '167', '1983-11-02'])
            data_written = dev_test.unified_newlines(delimited_stream.getvalue())
        self.assertEqual('%r' % 'Miller,173,1967-05-23\nWebster,167,1983-11-02\n', '%r' % data_written)

    def test_fails_on_writing_broken_field(self):
        with io.StringIO() as delimited_stream:
            with validio.Writer(self._standard_cid, delimited_stream) as delimited_writer:
                delimited_writer.write_row(['Miller', '173', '1967-05-23'])
                try:
                    delimited_writer.write_row(['Webster', 'not_a_number', '1983-11-02'])
                except errors.FieldValueError as anticipated_error:
                    dev_test.assert_fnmatches(
                        self, str(anticipated_error),
                        "* (R2C2): cannot accept field height: value must be an integer number: *'not_a_number'")
