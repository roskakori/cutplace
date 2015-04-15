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
from cutplace import interface
from cutplace import sql

import sqlite3
import unittest

_ANY_FORMAT = data.DataFormat(data.FORMAT_DELIMITED)
_FIXED_FORMAT = data.DataFormat(data.FORMAT_FIXED)


class SqlFactoryTest(unittest.TestCase):

    """
    Tests for sql factory
    """
    _TEST_ENCODING = "cp1252"

    def test_can_create_sql_factory(self):
        cid = interface.Cid()
        cid.read('customers', [
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

        sql_factory = sql.SqlFactory(cid, 'customers')
        self.assertEqual(cid.field_names, sql_factory.cid._field_names)

    def test_can_create_sql_create_statement(self):
        cid = interface.Cid()
        cid.read('customers', [
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

        sql_factory = sql.SqlFactory(cid, 'customers')
        self.maxDiff = None
        self.assertEqual(
            sql_factory.create_table_statement(),
            "create table customers (\n    branch_id varchar not null,"
            "\n    customer_id int not null,\n    first_name varchar,"
            "\n    surname varchar(60) not null,\n    gender varchar not null,"
            "\n    date_of_birth date not null\n);")

    def test_can_create_sql_create_statement_for_sqlite(self):
        cid = interface.Cid()
        cid.read('customers', [
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

        sql_factory = sql.SqlFactory(cid, 'customers')

        temp_database = None

        try:
            temp_database = sqlite3.connect(":memory:")
            cursor = temp_database.cursor()

            cursor.execute(sql_factory.create_table_statement())

        except sqlite3.Error as err:
            self.fail()
            return err

    def test_can_create_char_field(self):
        cid = interface.Cid()
        cid.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'surname', 'Doe', 'x', '1...60', 'Text'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers')

        for field in sql_factory.sql_fields():
            self.assertEqual(field[1], 'varchar')
            self.assertEqual(field[2], 60)
            self.assertEqual(field[4], True)

    def test_can_create_int_field(self):
        cid = interface.Cid()
        cid.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'customer_id', '12345', '', '', 'Integer', '0...99999'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers')

        for field in sql_factory.sql_fields():
            self.assertEqual(field[1], 'int')
            self.assertEqual(field[4], False)

    def test_can_create_date_field(self):
        cid = interface.Cid()
        cid.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'date_of_birth', '03.11.1969', '', '', 'DateTime', 'DD.MM.YYYY'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers')

        for field in sql_factory.sql_fields():
            self.assertEqual(field[1], 'date')
            self.assertEqual(field[4], False)

    def test_can_create_decimal_field(self):
        cid = interface.Cid()
        cid.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'latitude', '1.5853', '', '', 'Decimal'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers')

        for field in sql_factory.sql_fields():
            self.assertEqual(field[1], 'decimal')
            self.assertEqual(field[4], False)
