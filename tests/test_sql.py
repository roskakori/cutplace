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

import sqlite3
import unittest
from contextlib import closing

import six

from cutplace import data
from cutplace import interface
from cutplace import sql

_ANY_FORMAT = data.DataFormat(data.FORMAT_DELIMITED)
_FIXED_FORMAT = data.DataFormat(data.FORMAT_FIXED)


class SqlFactoryTest(unittest.TestCase):
    """
    Tests for SqlFactory.
    """
    _TEST_ENCODING = "cp1252"

    def _assert_is_valid_sqlite_statement(self, statement):
        assert statement is not None
        with closing(sqlite3.connect(':memory:')) as temp_database:
            with closing(temp_database.cursor()) as temp_cursor:
                try:
                    temp_cursor.execute(statement)
                except sqlite3.Error as error:
                    self.fail('cannot run statement: %s; statement=%r' % (error, statement))

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
            ['F', 'latitude', '1.5853', '', '', 'Decimal'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers')
        self.maxDiff = None
        self.assertEqual(
            sql_factory.create_table_statement(),
            "create table customers (\n    branch_id varchar not null,"
            "\n    customer_id int not null,\n    first_name varchar,"
            "\n    surname varchar(60) not null,\n    gender varchar not null,"
            "\n    date_of_birth date not null,"
            "\n    latitude decimal(31, 12) not null\n);")

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
        self._assert_is_valid_sqlite_statement(sql_factory.create_table_statement())

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

        for _, field_type, field_length, _, is_not_null, _ in sql_factory.sql_fields():
            self.assertEqual(field_type, 'varchar')
            self.assertEqual(field_length, 60)
            self.assertEqual(is_not_null, True)

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

        for _, field_type, _, _, is_not_null, _ in sql_factory.sql_fields():
            self.assertEqual(field_type, 'int')
            self.assertEqual(is_not_null, False)

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

        for _, field_type, _, _, is_not_null, _ in sql_factory.sql_fields():
            self.assertEqual(field_type, 'date')
            self.assertEqual(is_not_null, False)

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

        for _, field_type, _, _, is_not_null, _ in sql_factory.sql_fields():
            self.assertEqual(field_type, 'decimal')
            self.assertEqual(is_not_null, False)

    def test_can_handle_db2_dialect(self):
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
            ['F', 'small', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT)],
            ['F', 'int', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT + 1)],
            ['F', 'big', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_INTEGER + 1)],
            ['F', 'decimal', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_BIGINT + 1)],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers', sql.DB2_SQL_DIALECT)

        sql_fields = list(sql_factory.sql_fields())
        self.assertEqual(sql_fields[0][1], 'decimal')
        self.assertEqual(sql_fields[0][4], False)
        self.assertEqual(sql_fields[1][1], 'smallint')
        self.assertEqual(sql_fields[1][4], False)
        self.assertEqual(sql_fields[2][1], 'integer')
        self.assertEqual(sql_fields[2][4], False)
        self.assertEqual(sql_fields[3][1], 'bigint')
        self.assertEqual(sql_fields[3][4], False)
        self.assertEqual(sql_fields[4][1], 'decimal')
        self.assertEqual(sql_fields[4][4], False)

    def test_can_handle_ms_sql_dialect(self):
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
            ['F', 'smallint', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT)],
            ['F', 'int', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT + 1)],
            ['F', 'big', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_INTEGER + 1)],
            ['F', 'decimal', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_BIGINT + 1)],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers', sql.TRANSACT_SQL_DIALECT)

        sql_fields = list(sql_factory.sql_fields())
        self.assertEqual(sql_fields[0][1], 'decimal')
        self.assertEqual(sql_fields[0][4], False)
        self.assertEqual(sql_fields[1][1], 'smallint')
        self.assertEqual(sql_fields[1][4], False)
        self.assertEqual(sql_fields[2][1], 'int')
        self.assertEqual(sql_fields[2][4], False)
        self.assertEqual(sql_fields[3][1], 'bigint')
        self.assertEqual(sql_fields[3][4], False)
        self.assertEqual(sql_fields[4][1], 'decimal')
        self.assertEqual(sql_fields[4][4], False)

    def test_can_handle_oracle_sql_dialect(self):
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
            ['F', 'small', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT)],
            ['F', 'int', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_SMALLINT + 1)],
            ['F', 'big', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_INTEGER + 1)],
            ['F', 'decimal', '1', '', '', 'Integer', '0...%s' % six.text_type(sql.MAX_BIGINT + 1)],
            ['F', 'surname', 'Doe', '', '1...60', 'Text'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers', sql.PL_SQL_DIALECT)

        sql_fields = list(sql_factory.sql_fields())
        self.assertEqual(sql_fields[0][1], 'number')
        self.assertEqual(sql_fields[0][4], False)
        self.assertEqual(sql_fields[1][1], 'int')
        self.assertEqual(sql_fields[1][4], False)
        self.assertEqual(sql_fields[2][1], 'int')
        self.assertEqual(sql_fields[2][4], False)
        self.assertEqual(sql_fields[3][1], 'number')
        self.assertEqual(sql_fields[3][4], False)
        self.assertEqual(sql_fields[4][1], 'number')
        self.assertEqual(sql_fields[4][4], False)
        self.assertEqual(sql_fields[5][1], 'varchar2')

    def test_can_escape_keywords(self):
        cid = interface.Cid()
        cid.read('customers', [
            ['D', 'Format', 'delimited'],
            ['D', 'Line delimiter', 'any'],
            ['D', 'Item delimiter', ','],
            ['D', 'Quote character', '"'],
            ['D', 'Escape character', '\\'],
            ['D', 'Encoding', 'ISO-8859-1'],
            ['D', 'Allowed characters', '32:'],
            ['F', 'add', '1.5853', '', '', 'Decimal'],
        ])

        sql_factory = sql.SqlFactory(cid, 'customers', sql.PL_SQL_DIALECT)
        sql_field_name = list(sql_factory.sql_fields())[0][0]
        self.assertEqual(sql_field_name, '"add"')

        sql_factory = sql.SqlFactory(cid, 'customers', sql.ANSI_SQL_DIALECT)
        sql_field_name = list(sql_factory.sql_fields())[0][0]
        self.assertEqual(sql_field_name, '"add"')

        sql_factory = sql.SqlFactory(cid, 'customers', sql.TRANSACT_SQL_DIALECT)
        sql_field_name = list(sql_factory.sql_fields())[0][0]
        self.assertEqual(sql_field_name, '"add"')

        sql_factory = sql.SqlFactory(cid, 'customers', sql.DB2_SQL_DIALECT)
        sql_field_name = list(sql_factory.sql_fields())[0][0]
        self.assertEqual(sql_field_name, '"add"')
