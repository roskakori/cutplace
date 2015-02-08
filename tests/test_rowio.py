"""
Tests for the :py:mod:`cutplace.rowio` module.
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

from cutplace import data
from cutplace import interface
from cutplace import errors
from cutplace import rowio
from tests import dev_test

_EURO_SIGN = '\u20ac'


class _BaseRowsTest(unittest.TestCase):
    def _assert_rows_contain_data(self, rows):
        self.assertTrue(rows is not None)

        # Convert possible generator to list so it can be queried multiple times.
        rows_as_list = list(rows)

        self.assertTrue(len(rows_as_list) > 0)
        none_empty_rows = [row for row in rows_as_list if len(row) > 0]
        self.assertTrue(len(none_empty_rows) > 0)


class ExcelRowsTest(_BaseRowsTest):
    def test_can_read_excel_rows(self):
        excel_path = dev_test.path_to_test_data('valid_customers.xls')
        self._assert_rows_contain_data(rowio.excel_rows(excel_path))

    def test_can_extract_all_excel_field_types(self):
        field_types_path = dev_test.path_to_test_data('fieldtypes.xls')
        for row_number, row in enumerate(rowio.excel_rows(field_types_path)):
            self.assertEqual(3, len(row))
            if row_number >= 1:
                _, excel_value, cutplace_value = row
                self.assertEqual(cutplace_value, excel_value)

    def test_fails_on_excel_from_csv(self):
        csv_path = dev_test.path_to_test_data('valid_customers.csv')
        try:
            list(rowio.excel_rows(csv_path))
            self.fail()
        except errors.DataFormatError as anticipated_error:
            dev_test.assert_fnmatches(self, str(anticipated_error), '* (R1C1): cannot read Excel file: *')

    def test_fails_on_excel_from_ods(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        try:
            list(rowio.excel_rows(ods_path))
            self.fail()
        except errors.DataFormatError as anticipated_error:
            dev_test.assert_fnmatches(self, str(anticipated_error), '* (R1C1): cannot read Excel file: *')


class OdsRowsTest(_BaseRowsTest):
    def test_can_read_ods_rows(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        self._assert_rows_contain_data(rowio.ods_rows(ods_path))

    def test_fails_on_ods_from_csv(self):
        broken_ods_path = dev_test.path_to_test_data('customers.csv')
        try:
            list(rowio.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue(
                'cannot uncompress ODS spreadsheet:' in error_message, 'error_message=%r' % error_message)

    def test_fails_on_ods_without_content_xml(self):
        broken_ods_path = dev_test.path_to_test_data('broken_without_content_xml.ods')
        try:
            list(rowio.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue(
                'cannot extract content.xml' in error_message, 'error_message=%r' % error_message)

    def test_fails_on_ods_without_broken_content_xml(self):
        broken_ods_path = dev_test.path_to_test_data('broken_content_xml.ods')
        try:
            list(rowio.ods_rows(broken_ods_path))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue(
                'cannot parse content.xml' in error_message, 'error_message=%r' % error_message)

    def test_fails_on_non_existent_ods_sheet(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        try:
            list(rowio.ods_rows(ods_path, 123))
            self.fail('expected DataFormatError')
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue(
                'ODS must contain at least' in error_message, 'error_message=%r' % error_message)

    def test_fails_on_ods_from_excel(self):
        excel_path = dev_test.path_to_test_data('valid_customers.xls')
        try:
            list(rowio.ods_rows(excel_path))
            self.fail()
        except errors.DataFormatError as anticipated_error:
            dev_test.assert_fnmatches(self, str(anticipated_error), '*: cannot uncompress ODS spreadsheet: *')


class DelimitedRowsTest(_BaseRowsTest):
    def test_can_read_delimited_non_ascii(self):
        data_format = data.DataFormat(data.FORMAT_DELIMITED)
        data_format.validate()
        with io.StringIO('eggs\nsp\u00c4m') as data_stream:
            actual_rows = list(rowio.delimited_rows(data_stream, data_format))
        self.assertEqual([['eggs'], ['sp\u00c4m']], actual_rows)

    def test_fails_on_delimited_with_unterminated_quote(self):
        cid_path = dev_test.path_to_test_cid('customers.ods')
        customer_cid = interface.Cid(cid_path)
        broken_delimited_path = dev_test.path_to_test_data('broken_customers_with_unterminated_quote.csv')
        try:
            list(rowio.delimited_rows(broken_delimited_path, customer_cid.data_format))
        except errors.DataFormatError as error:
            error_message = '%s' % error
            self.assertTrue(
                'cannot parse delimited file' in error_message, 'error_message=%r' % error_message)


class FixedRowsTest(_BaseRowsTest):
    @staticmethod
    def _create_fixed_data_format_and_fields_for_name_and_height(line_delimiter='any', validate=True):
        """
        A tuple of ``(data_format, field_names_and_lengths)`` that can be
        passed to `iotools.fixed_rows()` and describes a fixed data format
        with 2 fields ``name``  and ``size``.
        """
        data_format = data.DataFormat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_LINE_DELIMITER, line_delimiter)
        if validate:
            data_format.validate()
        field_names_and_lengths = (
            ('name', 4),
            ('size', 3),
        )
        return data_format, field_names_and_lengths

    def test_can_read_fixed_rows(self):
        cid_path = dev_test.path_to_test_cid('customers_fixed.ods')
        customer_cid = interface.Cid(cid_path)
        fixed_path = dev_test.path_to_test_data('valid_customers_fixed.txt')
        field_names_and_lengths = interface.field_names_and_lengths(customer_cid)
        rows = list(rowio.fixed_rows(fixed_path, customer_cid.data_format.encoding, field_names_and_lengths))
        self.assertNotEqual(0, len(rows))
        for row_index in range(len(rows) - 1):
            row = rows[row_index]
            next_row = rows[row_index + 1]
            self.assertNotEqual(0, len(row))
            self.assertEqual(len(row), len(next_row))

    def _test_can_read_fixed_rows_from_stringio(self, data_text, data_format=None):
        assert (data_format is None) or data_format.is_valid

        default_data_format, field_names_and_lengths = \
            FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        actual_data_format = default_data_format if data_format is None else data_format
        with io.StringIO(data_text) as data_io:
            rows = list(rowio.fixed_rows(
                data_io, actual_data_format.encoding, field_names_and_lengths, actual_data_format.line_delimiter))
        self._assert_rows_contain_data(rows)
        for row in rows:
            for item in row:
                self.assertTrue(item in data_text, 'item %r must be part of data %r' % (item, data_text))

    def test_can_read_fixed_rows_with_any_line_delimiter(self):
        data_format, _ = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        self._test_can_read_fixed_rows_from_stringio('hugo172\nsepp163\n', data_format)

    def test_can_read_empty_fixed_rows(self):
        data_format = data.DataFormat(data.FORMAT_FIXED)
        data_format.validate()
        with io.StringIO('') as data_io:
            rows = list(rowio.fixed_rows(
                data_io, data_format.encoding, (('dummy', 1),), data_format.line_delimiter))
        self.assertEqual([], rows)

    def test_can_read_fixed_rows_with_crlf_line_delimiter_combinations(self):
        base_data_text = 'hugo172\nsepp163\n'
        for line_delimiter in ('\n', '\r', '\r\n'):
            line_delimiter_text = data.LINE_DELIMITER_TO_TEXT_MAP[line_delimiter]
            data_format, _ = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height(line_delimiter_text)
            data_text = base_data_text.replace('\n', line_delimiter)
            self._test_can_read_fixed_rows_from_stringio(data_text, data_format)

    def test_can_read_fixed_rows_with_missing_terminating_line_delimiter(self):
        data_format, field_names_and_lengths = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        with io.StringIO('hugo172\nsepp163') as data_io:
            rows = list(rowio.fixed_rows(
                data_io, data_format.encoding, field_names_and_lengths, data_format.line_delimiter))
        self._assert_rows_contain_data(rows)
        self.assertEqual(2, len(rows))

    def test_can_read_fixed_rows_with_mixed_line_delimiters(self):
        data_format, field_names_and_lengths = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        with io.StringIO('john172\rmary163\nbill167\r\njane184\r\n') as data_io:
            rows = list(rowio.fixed_rows(
                data_io, data_format.encoding, field_names_and_lengths, data_format.line_delimiter))
        self.assertEqual([['john', '172'], ['mary', '163'], ['bill', '167'], ['jane', '184']], rows)

    def test_can_read_fixed_rows_with_mixed_line_delimiters_terminated_by_carriage_return(self):
        data_format, field_names_and_lengths = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        with io.StringIO('john172\r\nmary163\r') as data_io:
            rows = list(rowio.fixed_rows(
                data_io, data_format.encoding, field_names_and_lengths, data_format.line_delimiter))
        self.assertEqual([['john', '172'], ['mary', '163']], rows)

    def _fails_on_fixed_rows_from_stringio(self, data_text, expected_error_pattern='*', data_format=None):
        assert (data_format is None) or data_format.is_valid

        default_data_format, field_names_and_lengths = \
            FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height()
        actual_data_format = default_data_format if data_format is None else data_format
        with io.StringIO(data_text) as data_io:
            rows = rowio.fixed_rows(
                data_io, actual_data_format.encoding, field_names_and_lengths, actual_data_format.line_delimiter)
            try:
                for _ in rows:
                    pass
                self.fail()
            except errors.DataFormatError as anticipated_error:
                dev_test.assert_fnmatches(self, str(anticipated_error), expected_error_pattern)

    def test_fails_on_fixed_rows_with_broken_line_delimiter(self):
        data_format, _ = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height('lf')
        self._fails_on_fixed_rows_from_stringio(
            'hugo172\tsepp163', r"*line delimiter is '\t' but must be '\n'", data_format)

    def test_fails_on_fixed_rows_with_broken_any_line_delimiter(self):
        self._fails_on_fixed_rows_from_stringio(
            'hugo172\tsepp163', r"*line delimiter is '\t' but must be one of: '\n', '\r' or '\r\n'")

    def test_fails_on_fixed_rows_with_incomplete_record(self):
        data_format, _ = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height('lf')
        self._fails_on_fixed_rows_from_stringio(
            'x', "*cannot read field 'name': need 4 characters but found only 1: 'x'", data_format)

    def test_fails_on_fixed_rows_with_missing_record(self):
        data_format, _ = FixedRowsTest._create_fixed_data_format_and_fields_for_name_and_height('lf')
        self._fails_on_fixed_rows_from_stringio(
            'john', "*after field 'name' 3 characters must follow for: 'size'", data_format)

    def test_can_read_fixed_rows_without_line_delimiter(self):
        data_format = data.DataFormat(data.FORMAT_FIXED)
        data_format.set_property(data.KEY_LINE_DELIMITER, 'none')
        data_format.validate()
        self._test_can_read_fixed_rows_from_stringio('hugo172sepp163', data_format)

    def test_can_auto_read_excel_rows(self):
        excel_path = dev_test.path_to_test_data('valid_customers.xls')
        self._assert_rows_contain_data(rowio.auto_rows(excel_path))


class AutoRowsTest(_BaseRowsTest):
    def test_can_auto_read_ods_rows(self):
        ods_path = dev_test.path_to_test_data('valid_customers.ods')
        self._assert_rows_contain_data(rowio.auto_rows(ods_path))


class DelimitedRowWriterTest(unittest.TestCase):
    def test_can_write_delimited_data_to_string_io(self):
        delimited_data_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_data_format.validate()
        with io.StringIO() as target:
            with rowio.DelimitedRowWriter(target, delimited_data_format) as delimited_writer:
                delimited_writer.write_row(['a', 'b', _EURO_SIGN])
                delimited_writer.write_row([])
                delimited_writer.write_row([1, 2, 'end'])
            data_written = dev_test.unified_newlines(target.getvalue())
        self.assertEqual('%r' % data_written, '%r' % 'a,b,\u20ac\n\n1,2,end\n')

    def test_can_write_delimited_data_to_path(self):
        delimited_data_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_data_format.set_property(data.KEY_ENCODING, 'utf-8')
        delimited_data_format.validate()
        delimited_path = dev_test.path_to_test_result('test_can_write_delimited_to_path.csv')
        with io.open(delimited_path, 'w', newline='', encoding=delimited_data_format.encoding) as delimited_target_stream:
            with rowio.DelimitedRowWriter(delimited_target_stream, delimited_data_format) as delimited_writer:
                delimited_writer.write_row(['a', 'b', _EURO_SIGN])
                delimited_writer.write_row([])
                delimited_writer.write_row([1, 2, 'end'])
        with io.open(delimited_path, 'r', encoding=delimited_data_format.encoding) as delimited_source_stream:
            # Note: all kinds of newline characters are translated to '\n' because of newline=None.
            data_written = delimited_source_stream.read()
        self.assertEqual('%r' % data_written, '%r' % 'a,b,\u20ac\n\n1,2,end\n')

    def test_fails_on_unicode_error_during_delimited_write(self):
        delimited_data_format = data.DataFormat(data.FORMAT_DELIMITED)
        delimited_data_format.set_property(data.KEY_ENCODING, 'ascii')
        delimited_data_format.validate()
        delimited_path = dev_test.path_to_test_result('test_fails_on_unicode_error_during_delimited_write.csv')
        with io.open(delimited_path, 'w', newline='', encoding=delimited_data_format.encoding) as delimited_target_stream:
            with rowio.DelimitedRowWriter(delimited_target_stream, delimited_data_format) as delimited_writer:
                try:
                    delimited_writer.write_row(['a'])
                    delimited_writer.write_row(['b', _EURO_SIGN])
                    self.fail()
                except errors.DataError as anticipated_error:
                    anticipated_error_message = str(anticipated_error)
                    dev_test.assert_fnmatches(
                        self, anticipated_error_message, "*.csv (R2C1): cannot write data row: *; row=*'b', *")


class FixedRowWriterTest(unittest.TestCase):
    def test_can_write_fixed_data_to_string(self):
        fixed_data_format = data.DataFormat(data.FORMAT_FIXED)
        fixed_data_format.set_property(data.KEY_ENCODING, 'utf-8')
        fixed_data_format.validate()
        field_names_and_lengths = [('a', 1), ('b', 3)]
        with io.StringIO() as target:
            with rowio.FixedRowWriter(target, fixed_data_format, field_names_and_lengths) as fixed_writer:
                fixed_writer.write_row(['a', 'bcd'])
                fixed_writer.write_row([_EURO_SIGN, '   '])
            data_written = dev_test.unified_newlines(target.getvalue())
        self.assertEqual('%r' % data_written, '%r' % 'abcd\n\u20ac   \n')

    def test_can_write_fixed_data_without_line_delimiter(self):
        fixed_data_format = data.DataFormat(data.FORMAT_FIXED)
        fixed_data_format.set_property(data.KEY_LINE_DELIMITER, 'none')
        fixed_data_format.validate()
        with io.StringIO() as target:
            with rowio.FixedRowWriter(target, fixed_data_format, [('x', 1)]) as fixed_writer:
                fixed_writer.write_rows([['1'], ['2'], ['3']])
            data_written = target.getvalue()
        self.assertEqual(data_written, '123')

    def test_fails_on_unicode_error_during_fixed_write(self):
        fixed_data_format = data.DataFormat(data.FORMAT_FIXED)
        fixed_data_format.set_property(data.KEY_ENCODING, 'ascii')
        fixed_data_format.validate()
        fixed_path = dev_test.path_to_test_result('test_fails_on_unicode_error_during_fixed_write.txt')
        with rowio.FixedRowWriter(fixed_path, fixed_data_format, [('x', 1)]) as fixed_writer:
            fixed_writer.write_row(['a'])
            try:
                fixed_writer.write_row([_EURO_SIGN])
                self.fail()
            except errors.DataError as anticipated_error:
                anticipated_error_message = str(anticipated_error)
                dev_test.assert_fnmatches(
                    self, anticipated_error_message, "*.txt (R2C1): cannot write data row: *; row=*")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
