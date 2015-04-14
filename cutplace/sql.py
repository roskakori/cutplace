"""
Methods to create sql statements from existing fields.
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

import io
import logging
import os.path

from cutplace import rowio

# TODO: Move to module ``ranges``.
MAX_SMALLINT = 2 ** 15 - 1
MAX_INTEGER = 2 ** 31 - 1
MAX_BIGINT = 2 ** 63 - 1

#: SQL dialect: ANSI SQL
ANSI = 'ansi'
#: SQL dialect: DB2 by IBM
DB2 = "db2"
#: SQL dialect: Microsoft SQL
MSSQL = "mssql"
#: SQL dialect: ANSI MySQL / MariaDB
MYSQL = "mysql"
#: SQL dialect: Oracle
ORACLE = "oracle"

_log = logging.getLogger("cutplace")


def assert_is_valid_dialect(dialect):
    assert dialect in (ANSI, DB2, MSSQL, MYSQL, ORACLE), 'dialect=%r' % dialect


def write_create(cid_path, cid_reader):
    # TODO: Add option for different cid types.
    cid_reader.read(cid_path, rowio.excel_rows(cid_path))

    create_path = os.path.splitext(cid_path)[0] + '_create.sql'
    # TODO: Add option to specify target folder for SQL files.
    _log.info('write SQL create statements to "%s"', create_path)
    with io.open(create_path, 'w', encoding='utf-8') as create_file:
        # TODO: Add option for encoding.
        sql_factory = SqlFactory(cid_reader, os.path.splitext(cid_path)[0])
        create_file.write(sql_factory.create_table_statement())
        # TODO: Add option for target SQL dialect


class SqlFactory(object):
    def __init__(self, cid, table, dialect=ANSI):
        self._cid = cid
        self._table = table
        self._dialect = dialect

        assert_is_valid_dialect(self._dialect)

    @property
    def cid(self):
        return self._cid

    def sql_fields(self):
        """
        Tuples `(field_name, field_type, length, precision, is_not_null, default_value)`
        """
        for field in self._cid.field_formats:
            sql_type, sql_length, sql_precision = (field.sql_ansi_type() + (None, None))[:3]
            assert sql_type in ('varchar', 'decimal', 'int', 'date')

            row = (field.field_name, sql_type, sql_length, sql_precision, field.is_allowed_to_be_empty,
                   field.empty_value)
            yield row

    def create_table_statement(self):
        result = "create table " + self._table + " (\n"
        first_field = True

        # get column definitions for all fields
        for field_name, field_type, length, precision, is_not_null, default_value in self.sql_fields():
            if not first_field:
                result += ",\n"

            column_def = field_name + " " + field_type
            if length is not None and precision is None:
                column_def += "(" + str(length) + ")"
            elif length is not None and precision is not None:
                column_def += "(" + str(length) + ", " + str(precision) + ")"

            if not is_not_null:
                column_def += " not null"

            if default_value is not None and len(default_value) > 0:
                column_def += " default " + str(default_value)

            result += column_def

            if first_field:
                first_field = False

        result += ");"

        return result

    def create_index_statements(self):
        pass

    def create_constraint_statements(self):
        pass
