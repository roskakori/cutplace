"""
Tests for `sql` module
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

from cutplace import data
from cutplace import fields
from cutplace import interface
from cutplace import sql
from cutplace import validio
from tests import dev_test

import unittest

_ANY_FORMAT = data.DataFormat(data.FORMAT_DELIMITED)
_FIXED_FORMAT = data.DataFormat(data.FORMAT_FIXED)


class SqlTest(unittest.TestCase):

    """
    Tests for sql module
    """
    _TEST_ENCODING = "cp1252"

    def test_can_output_sql_date(self):
        field_format = fields.DateTimeFieldFormat("x", True, None, "YYYY-MM-DD", _ANY_FORMAT)
        self.assertEqual(field_format.as_sql(sql.MSSQL)[0], "x date")

    def test_can_output_sql_time(self):
        field_format = fields.DateTimeFieldFormat("x", True, None, "hh:mm:ss", _ANY_FORMAT)
        self.assertEqual(field_format.as_sql(sql.MSSQL)[0], "x time")

    def test_can_output_sql_datetime(self):
        field_format = fields.DateTimeFieldFormat("x", True, None, "YYYY:MM:DD hh:mm:ss", _ANY_FORMAT)
        self.assertEqual(field_format.as_sql(sql.MSSQL)[0], "x datetime")
        field_format = fields.DateTimeFieldFormat("x", True, None, "YY:MM:DD hh:mm:ss", _ANY_FORMAT)
        self.assertEqual(field_format.as_sql(sql.MSSQL)[0], "x datetime")

    def test_can_output_sql_datetime_not_null(self):
        field_format = fields.DateTimeFieldFormat("x", False, None, "YYYY:MM:DD hh:mm:ss", _ANY_FORMAT)
        self.assertEqual(field_format.as_sql(sql.MSSQL)[0], "x datetime not null")

    def test_can_output_sql_varchar_choice(self):
        field_format = fields.ChoiceFieldFormat("color", True, None, "red,grEEn, blue ", _ANY_FORMAT)
        column_def, constraint = field_format.as_sql(sql.MSSQL)
        self.assertEqual(column_def, "color varchar(255)")
        self.assertEqual(constraint, "constraint chk_rule_color check( color in ('red','grEEn','blue') )")

    def test_can_output_sql_smallint_choice(self):
        field_format = fields.ChoiceFieldFormat("color", True, None, "1,2, 3 ", _ANY_FORMAT)
        column_def, constraint = field_format.as_sql(sql.MSSQL)
        self.assertEqual(column_def, "color smallint")
        self.assertEqual(constraint, "constraint chk_rule_color check( color in (1,2,3) )")

    # TODO: def test_can_represent_string_constant_as_sql(self):
    #     field_format = fields.ConstantFieldFormat('fixed', False, None, 'some', _ANY_FORMAT)
    #     column_def, constraint = field_format.as_sql(sql.MSSQL)
    #     self.assertEqual(column_def, 'TODO')
    #     self.assertEqual(constraint, 'TODO')

    # TODO: def test_can_represent_integer_constant_as_sql(self):
    #     field_format = fields.ConstantFieldFormat('fixed', False, None, '1', _ANY_FORMAT)
    #     column_def, constraint = field_format.as_sql(sql.MSSQL)
    #     self.assertEqual(column_def, 'TODO')
    #     self.assertEqual(constraint, 'TODO')

    def test_can_output_sql_integer(self):
        field_format = fields.ChoiceFieldFormat("color", True, None, "1000000,2, 3 ", _ANY_FORMAT)
        column_def, constraint = field_format.as_sql(sql.MSSQL)
        self.assertEqual(column_def, "color integer")
        self.assertEqual(constraint, "constraint chk_rule_color check( color in (1000000,2,3) )")

    def test_can_output_sql_bigint(self):
        field_format = fields.ChoiceFieldFormat("color", True, None, "10000000000,2, 3 ", _ANY_FORMAT)
        column_def, constraint = field_format.as_sql(sql.MSSQL)
        self.assertEqual(column_def, "color bigint")
        self.assertEqual(constraint, "constraint chk_rule_color check( color in (10000000000,2,3) )")

    def test_can_output_sql_without_range(self):
        field_format = fields.PatternFieldFormat("x", False, None, "h*g?", _ANY_FORMAT)
        column_def, constraint = field_format.as_sql(sql.MSSQL)
        self.assertEqual(column_def, "x varchar(255) not null")
        self.assertEqual(constraint, "")

    def test_can_create_sql_statement(self):
        cid_reader = interface.Cid()
        cid_reader.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'branch_id', '38123', '', '', 'RegEx'],
            ['F', 'customer_id', '12345', '', '', 'Integer', '0...99999'],
            ['F', 'first_name', 'John', 'X', '', 'Text'],
            ['F', 'surname', 'Doe', '', '1...60', 'Text'],
            ['F', 'gender', 'male', '', '', 'Choice', 'male, female, unknown'],
            ['F', 'date_of_birth', '03.11.1969', '', '', 'DateTime', 'DD.MM.YYYY'],
        ])
        self.maxDiff = None
        self.assertEqual(
            sql.as_sql_create_table(cid_reader, sql.MYSQL),
            "create table customers (\nbranch_id varchar(255) not null,"
            "\ncustomer_id integer not null,\nfirst_name varchar(255),"
            "\nsurname varchar(60) not null,\ngender varchar(255) not null,"
            "\ndate_of_birth date not null,"
            "\nconstraint chk_customer_id check( ( customer_id between 0 and 99999 ) ),"
            "\nconstraint chk_length_surname check (length(surname >= 1) and length(surname <= 60)),"
            "\nconstraint chk_rule_gender check( gender in ('male','female','unknown') )\n);")

        print(sql.as_sql_create_table(cid_reader, sql.MYSQL))

        # check if create insert statements works
        with validio.Reader(cid_reader, dev_test.path_to_test_data("valid_customers.csv")) as reader:
            print('\n'.join(list(sql.as_sql_create_inserts(cid_reader, reader))))
            self.assertEqual(
                list(sql.as_sql_create_inserts(cid_reader, reader)),
                ["insert into customers(branch_id, customer_id, first_name, surname, gender, date_of_birth) "
                 "values ('38000', 23, 'John', 'Doe', 'male', '08.03.1957');",
                 "insert into customers(branch_id, customer_id, first_name, surname, gender, date_of_birth) "
                 "values ('38000', 59, 'Jane', 'Miller', 'female', '04.10.1946');",
                 "insert into customers(branch_id, customer_id, first_name, surname, gender, date_of_birth) "
                 "values ('38053', 17, 'Mike', 'Webster', 'male', '23.12.1974');"])
