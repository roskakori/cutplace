"""
Tests for `cid` module
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

import fnmatch
import os.path
import unittest

import six

from cutplace import checks
from cutplace import interface
from cutplace import data
from cutplace import errors
from cutplace import fields
from cutplace import ranges
from cutplace import rowio
from tests import dev_test


class CidTest(unittest.TestCase):

    """
    Tests for cid module
    """
    _TEST_ENCODING = "cp1252"

    def test_can_create_empty_cid(self):
        cid = interface.Cid()
        cid_name = os.path.splitext(os.path.basename(cid._location.file_path))[0]
        self.assertEqual('test_interface', cid_name)

    def test_can_read_excel_and_create_data_format_delimited(self):
        cid_reader = interface.Cid()
        source_path = dev_test.CID_CUSTOMERS_XLS_PATH
        cid_reader.read(source_path, rowio.excel_rows(source_path))

        self.assertEqual(cid_reader._data_format.format, "delimited")
        self.assertEqual(cid_reader._data_format.header, 1)

    def test_fails_on_empty_data_format_property_name(self):
        cid_reader = interface.Cid()
        self.assertRaises(errors.InterfaceError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d', '', ''],
        ])

    def test_fails_on_missing_data_format_property_value(self):
        cid_reader = interface.Cid()
        self.assertRaises(errors.InterfaceError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d', 'header'],
        ])

    def test_fails_on_missing_data_format_property_name(self):
        cid_reader = interface.Cid()
        self.assertRaises(errors.InterfaceError, cid_reader.read, 'inline', [
            ['d', 'format', 'delimited'],
            ['d'],
        ])

    def test_fails_on_invalid_row_typ(self):
        cid_reader = interface.Cid()
        self.assertRaises(errors.InterfaceError, cid_reader.read, 'inline', [['x']])

    def test_can_skip_empty_rows(self):
        cid_reader = interface.Cid()
        cid_reader.read('inline', [
            [],
            [''],
            ['d', 'format', 'delimited'],
            ['f', 'some'],
        ])
        self.assertEqual(cid_reader._data_format.format, "delimited")

    def test_can_read_field_type_text_field(self):
        cid_reader = interface.Cid()
        cid_reader.read('inline', [
            ['d', 'format', 'delimited'],
            ['f', 'branch_id', '38000', '', '5']])
        self.assertEqual(cid_reader.field_names[0], 'branch_id')
        self.assertEqual(cid_reader.field_formats[0].length.description, ranges.Range('5').description)

    def test_can_read_fields_from_excel(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid('cid_customers.xls')
        cid_reader.read(source_path, rowio.excel_rows(source_path))
        self.assertEqual(cid_reader.field_names[0], 'customer_id')
        self.assertTrue(isinstance(cid_reader.field_formats[0], fields.IntegerFieldFormat))
        self.assertEqual(cid_reader.field_names[1], 'surname')
        self.assertTrue(isinstance(cid_reader.field_formats[1], fields.TextFieldFormat))
        self.assertEqual(cid_reader.field_formats[1].length.items, ranges.Range('...60').items)
        self.assertEqual(cid_reader.field_names[2], 'first_name')
        self.assertTrue(isinstance(cid_reader.field_formats[2], fields.TextFieldFormat))
        self.assertEqual(cid_reader.field_formats[2].length.items, ranges.Range('...60').items)
        self.assertTrue(cid_reader.field_formats[2].is_allowed_to_be_empty)
        self.assertEqual(cid_reader.field_names[3], 'date_of_birth')
        self.assertTrue(isinstance(cid_reader.field_formats[3], fields.DateTimeFieldFormat))
        self.assertEqual(cid_reader.field_names[4], 'gender')
        self.assertTrue(isinstance(cid_reader.field_formats[4], fields.ChoiceFieldFormat))
        self.assertTrue(cid_reader.field_formats[4].is_allowed_to_be_empty)

    def test_can_handle_all_field_formats_from_array(self):
        cid_reader = interface.Cid()
        cid_reader.read('inline', [
            ['d', 'format', 'delimited'],
            ['f', 'int', '', '', '', 'Integer'],
            ['f', 'choice', '', '', '', 'Choice', 'x,y'],
            ['f', 'date', '', '', '', 'DateTime'],
            ['f', 'dec', '', '', '', 'Decimal', ''],
            ['f', 'text']
        ])
        self.assertTrue(isinstance(cid_reader.field_formats[0], fields.IntegerFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[1], fields.ChoiceFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[2], fields.DateTimeFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[3], fields.DecimalFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[4], fields.TextFieldFormat))

    def test_can_handle_all_field_formats_from_excel(self):
        cid_reader = interface.Cid()
        source_path = dev_test.path_to_test_cid("alltypes.xls")
        cid_reader.read(source_path, rowio.excel_rows(source_path))
        self.assertTrue(isinstance(cid_reader.field_formats[0], fields.IntegerFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[1], fields.TextFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[2], fields.ChoiceFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[3], fields.DateTimeFieldFormat))
        self.assertTrue(isinstance(cid_reader.field_formats[4], fields.DecimalFieldFormat))

    def test_fails_on_empty_field_name(self):
        cid_to_read = interface.Cid()
        self.assertRaises(
            errors.InterfaceError, cid_to_read.read, 'inline', [
                ['d', 'format', 'delimited'],
                ['f', '', '38000', '', '5']
            ])

    def test_fails_on_numeric_field_name(self):
        cid_to_read = interface.Cid()
        self.assertRaises(
            errors.InterfaceError, cid_to_read.read, 'inline', [
                ['d', 'format', 'delimited'],
                ['f', '3', '38000', '', '5']
            ])

    def test_fails_on_special_character_as_field_name(self):
        cid_to_read = interface.Cid()
        self.assertRaises(
            errors.InterfaceError, cid_to_read.read, 'inline', [
                ['d', 'format', 'delimited'],
                ['f', '%', '38000', '', '5']
            ])

    def test_fails_on_python_keyword_as_field_name(self):
        cid_to_read = interface.Cid()
        self.assertRaises(
            errors.InterfaceError, cid_to_read.read, 'inline', [
                ['d', 'format', 'delimited'],
                ['f', 'class', '38000', '', '5']
            ])

    def test_can_read_delimited_rows(self):
        # TODO: either get rid of the CID and move it to test_iotools or use validate.Reader and move it to test_validate.
        delimited_cid = interface.Cid(dev_test.CID_CUSTOMERS_ODS_PATH)
        delimited_rows = rowio.delimited_rows(dev_test.CUSTOMERS_CSV_PATH, delimited_cid.data_format)
        title_row = next(delimited_rows)
        self.assertEqual(title_row, ['customer_id', 'surname', 'first_name', 'born', 'gender'])
        first_data_row = next(delimited_rows)
        self.assertEqual(first_data_row, ['1', 'Beck', 'Tyler', '1995-11-15', 'male'])

    def test_can_handle_checks_from_excel(self):
        cid_reader = interface.Cid()
        source_path = dev_test.CID_CUSTOMERS_XLS_PATH
        cid_reader.read(source_path, rowio.excel_rows(source_path))
        self.assertTrue(isinstance(cid_reader.check_for(cid_reader.check_names[0]), checks.IsUniqueCheck))

    def test_can_be_rendered_as_str(self):
        customers_cid = interface.Cid(dev_test.CID_CUSTOMERS_ODS_PATH)
        cid_str = str(customers_cid)
        self.assertTrue('Cid' in cid_str)
        self.assertTrue(data.FORMAT_DELIMITED in cid_str)
        self.assertTrue(customers_cid.field_names[0] in cid_str)

    def test_can_create_cid_from_text(self):
        cid_text = '\n'.join([
            ',Example CID as CSV from a string',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,name         ,,,...50',
            'F,height       ,,,      ,Decimal',
            'F,date_of_birth,,,      ,DateTime,YYYY-MM-DD',
        ])
        cid_from_text = interface.create_cid_from_string(cid_text)
        self.assertEqual(data.FORMAT_DELIMITED, cid_from_text.data_format.format)

    def test_can_access_field_information(self):
        cid_text = '\n'.join([
            ',Example CID as CSV from a string',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,name         ,,,...50',
            'F,height       ,,,      ,Decimal',
            'F,date_of_birth,,,      ,DateTime,YYYY-MM-DD',
        ])
        cid = interface.create_cid_from_string(cid_text)
        self.assertEqual(['name', 'height', 'date_of_birth'], cid.field_names)
        self.assertEqual(1, cid.field_index('height'))
        self.assertEqual('173', cid.field_value_for('height', ['hugo', '173', '1963-02-05']))
        self.assertEqual('height', cid.field_format_for('height').field_name)

    def _test_fails_on_broken_cid_from_text(self, cid_text, anticipated_error_message_pattern=None):
        assert cid_text is not None
        try:
            interface.create_cid_from_string(cid_text)
            self.fail('InterfaceError must be raised')
        except errors.InterfaceError as anticipated_error:
            if anticipated_error_message_pattern is not None:
                anticipated_error_message = six.text_type(anticipated_error)
                if not fnmatch.fnmatch(anticipated_error_message, anticipated_error_message_pattern):
                    self.fail(
                        'anticipated error message must match %r but is %r'
                        % (anticipated_error_message_pattern, anticipated_error_message)
                    )

    def test_fails_on_empty_cid_from_text(self):
        self._test_fails_on_broken_cid_from_text('', '*data format must be specified*')

    def test_fails_on_no_format_for_data_format(self):
        cid_text = '\n'.join([
            ',CID referring to an unknown data format',
            'D,encoding,ascii',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*: first data format row must set property 'format' instead of 'encoding'")

    def test_fails_on_unknown_data_format(self):
        cid_text = '\n'.join([
            ',CID referring to an unknown data format',
            'D,Format,no_such_format',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*format is no_such_format but must be on of*')

    def test_fails_on_duplicate_data_format(self):
        cid_text = '\n'.join([
            ',CID where the data format is set twice',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'D,Format,%s' % data.FORMAT_DELIMITED,
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*data format already is 'delimited' and must be set only once")

    def test_fails_on_field_before_data_format(self):
        cid_text = '\n'.join([
            ',CID where a field is declared before the data format',
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,',
            'D,Format,%s' % data.FORMAT_DELIMITED,
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*data format must be specified before first field*')

    def test_fails_on_check_before_data_format_and_fields(self):
        cid_text = '\n'.join([
            ',CID where a check is declared ahead of the data format and fields',
            'C,some_is_unique,IsUnique,some'
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*field names must be specified before check*')

    def test_fails_on_check_before_fields(self):
        cid_text = '\n'.join([
            ',CID where a check is declared ahead of any fields',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'C,some_is_unique,IsUnique,some'
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*field names must be specified before check*')

    def test_fails_on_unknown_field_type(self):
        cid_text = '\n'.join([
            ',CID referring to a field with a type for which there is no class',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,NoSuchType',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*cannot find class*')

    def test_fails_on_broken_field_rule(self):
        cid_text = '\n'.join([
            ',CID with a broken Integer field rule.',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,Integer ,no_integer_range',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, "*cannot declare field 'some':*")

    def test_fails_on_broken_field_name(self):
        cid_text = '\n'.join([
            ',CID referring to a field with a type for which there is no class',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name,,,Length,Type    ,Rule',
            'F,?',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*field name must begin with a lower-case letter but is: '?'")

    def test_fails_on_no_fields_at_all(self):
        cid_text = '\n'.join([
            ',CID without any fields at all',
            'D,Format,%s' % data.FORMAT_DELIMITED,
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*fields must be specified*')

    def test_fails_on_duplicate_field_name(self):
        cid_text = '\n'.join([
            ',CID where a field is declared twice with the same name',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,duplicate    ,,,      ,        ,',
            'F,duplicate    ,,,      ,        ,',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*duplicate field name must be changed to a unique one: duplicate')

    def test_fails_on_broken_example(self):
        cid_text = '\n'.join([
            ',CID with a broken example for a field',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,   ,,Length,Type    ,Rule',
            'F,some         ,abc,,      ,Integer',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*cannot validate example for field *: value must be an integer number*')

    def test_fails_on_lower_field_length_less_than_0(self):
        cid_text = '\n'.join([
            ',CID with a field that can have less than 0 characters',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,-1:   ,',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*lower limit for length of field * must be at least 0 but is: -1')

    def test_fails_on_upper_field_length_less_than_0(self):
        cid_text = '\n'.join([
            ',CID with a field that can have less than 0 characters',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,:-1   ,',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*upper limit for length of field * must be at least 0 but is: -1')

    def test_fails_on_missing_fixed_field_length(self):
        cid_text = '\n'.join([
            ',CID with a fixed field without length',
            'D,Format,%s' % data.FORMAT_FIXED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,      ,',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*length of field * must be specified with fixed data format')

    def test_fails_on_fixed_field_length_less_than_1(self):
        cid_text = '\n'.join([
            ',CID with a field that has less than 1 character',
            'D,Format,%s' % data.FORMAT_FIXED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,0    ,',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*length of field * for fixed data format must be at least 1 but is: 0')

    def test_fails_on_range_for_fixed_field_length(self):
        cid_text = '\n'.join([
            ',CID with a range as fixed field length',
            'D,Format,%s' % data.FORMAT_FIXED,
            ' ,Name         ,,,Length,Type    ,Rule',
            'F,some         ,,,1...',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*: length of field 'some' for fixed data format must be a specific number but is: 1...")

    def test_fails_on_broken_mark_for_empty_field(self):
        cid_text = '\n'.join([
            ',CID with a field that can be empty but is not marked with X',
            'D,Format,%s' % data.FORMAT_FIXED,
            ' ,Name         ,,Empty?,Length,Type,Rule',
            'F,some         ,,broken',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, '*mark for empty field must be * or empty but is *')

    def test_fails_on_check_without_description(self):
        cid_text = '\n'.join([
            ',CID with a check without a description',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'F,some',
            'C',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text, '*check description must be specified')

    def test_fails_on_check_without_type(self):
        cid_text = '\n'.join([
            ',CID with a check without a type',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'F,some',
            'C,check_without_type',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*check type is '' but must be one of: *'DistinctCountCheck'*'IsUniqueCheck'*")

    def test_fails_on_check_without_rule(self):
        cid_text = '\n'.join([
            ',CID with a check without a description',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'F,some',
            'C,check_without_rule,IsUnique',
        ])
        self._test_fails_on_broken_cid_from_text(cid_text)

    def test_fails_on_duplicate_check_declaration(self):
        cid_text = '\n'.join([
            ',CID with the same check declared twice',
            'D,Format,%s' % data.FORMAT_DELIMITED,
            'F,some',
            'C,duplicate_check,IsUnique,some',
            'C,duplicate_check,IsUnique,some',
        ])
        self._test_fails_on_broken_cid_from_text(
            cid_text, "*check description must be used only once: 'duplicate_check' (see also: *: first declaration)")


if __name__ == '__main__':
    unittest.main()
