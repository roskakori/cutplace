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

import os.path
import sqlite3

from cutplace import _tools
from cutplace import ranges

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


def assert_is_valid_dialect(dialect):
    assert dialect in (ANSI, DB2, MSSQL, MYSQL, ORACLE), 'dialect=%r' % dialect


def generate_choices(rule):
    choices = []

    # Split rule into tokens, ignoring white space.
    tokens = _tools.tokenize_without_space(rule)

    # Extract choices from rule tokens.
    # TODO: Handle comma after comma without choice.
    # previous_toky = None
    toky = next(tokens)
    while not _tools.is_eof_token(toky):
        if _tools.is_comma_token(toky):
            # TODO: Handle comma after comma without choice.
            # if previous_toky:
            #     previous_toky_text = previous_toky[1]
            # else:
            #     previous_toky_text = None
            pass
        choice = _tools.token_text(toky)
        choices.append(choice)
        toky = next(tokens)
        if not _tools.is_eof_token(toky):
            # Process next choice after comma.
            toky = next(tokens)

    return choices


def as_sql_text(field_name, field_is_allowed_to_be_empty, field_length, field_rule, field_empty_value, db):
    constraint = ""

    if field_length.items is not None:
        column_def = field_name + " varchar(" + str(field_length.upper_limit) + ")"
        if field_length.lower_limit is not None and field_length.upper_limit is not None:
            constraint = "constraint chk_length_" + field_name + " check (length(" + field_name + " >= " \
                + str(field_length.lower_limit) + ") and length(" + field_name + " <= " \
                + str(field_length.upper_limit) + "))"
        elif field_length.lower_limit is not None:
            constraint = "constraint chk_length_" + field_name + " check (length(" + field_name + " >= " \
                + str(field_length.lower_limit) + "))"
        elif field_length.upper_limit is not None:
            constraint = "constraint chk_length_" + field_name + " check (length(" + field_name + " <= " \
                + str(field_length.upper_limit) + "))"
    else:
        column_def = field_name + " varchar(255)"

    if field_rule is not None:
        choices = generate_choices(field_rule)

        if all(choice.isnumeric() for choice in choices):
            column_def = as_sql_number(field_name, field_is_allowed_to_be_empty, field_length, field_rule, None, db)[0]
            constraint += "constraint chk_rule_" + field_name + " check( " + field_name + " in (" \
                + ",".join(map(str, choices)) + ") )"
        else:
            constraint += "constraint chk_rule_" + field_name + " check( " + field_name + " in ('" \
                + "','".join(map(str, choices)) + "') )"

    if not field_is_allowed_to_be_empty:
        column_def += " not null"

    return [column_def, constraint]


def as_sql_number(field_name, field_is_allowed_to_be_empty, field_length, field_rule, range_rule, db):
    if range_rule is None:
        range_rule = ranges.Range(field_rule, ranges.DEFAULT_INTEGER_RANGE_TEXT)

    column_def = ""

    if (field_rule == '') and (field_length.description is not None):
        range_limit = 10 ** max([item[1] for item in field_length.items])  # get the highest integer of the range
    else:
        range_limit = max([rule[1] for rule in range_rule.items])  # get the highest integer of the range

    if range_limit <= MAX_SMALLINT:
        column_def = field_name + " smallint"
    elif range_limit <= MAX_INTEGER:
        column_def = field_name + " integer"
    else:
        if db in (MSSQL, DB2) and range_limit <= MAX_BIGINT:
            column_def = field_name + " bigint"
        else:
            """column_def, _ = DecimalFieldFormat(self._field_name, self._is_allowed_to_be_empty,
                                               self._length.description, self._rule, self._data_format,
                                               self._empty_value).as_sql(db)"""

    if not field_is_allowed_to_be_empty:
        column_def += " not null"

    constraint = ""
    for i in range(len(range_rule.items)):
        if i == 0:
            constraint = "constraint chk_" + field_name + " check( "
        constraint += "( " + field_name + " between " + str(range_rule.lower_limit) + " and " + \
                      str(range_rule.upper_limit) + " )"
        if i < len(range_rule.items) - 1:
            constraint += " or "
        else:
            constraint += " )"

    return [column_def, constraint]


def as_sql_date(field_name, field_is_allowed_to_be_empty, human_readable_format, db):
    column_def = ""
    constraint = ""

    if "hh" in human_readable_format and "YY" in human_readable_format:
        column_def = field_name + " datetime"
    elif "hh" in human_readable_format:
        column_def = field_name + " time"
    else:
        column_def = field_name + " date"

    if not field_is_allowed_to_be_empty:
        column_def += " not null"

    return [column_def, constraint]


def as_sql_create_table(cid, dialect='ansi'):
    assert_is_valid_dialect(dialect)

    file_name = os.path.basename(cid._cid_path)
    table_name = file_name.split('.')

    result = "create table " + table_name[0] + " (\n"
    constraints = ""

    # get column definitions and constraints for all fields
    for field in cid._field_formats:
        column_def, constraint = field.as_sql(dialect)
        result += column_def + ",\n"

        if len(constraint) > 0:
            constraints += constraint + ",\n"

    constraints = constraints.rsplit(',', 1)[0]

    result += constraints

    result += "\n);"

    temp_database = None

    try:
        temp_database = sqlite3.connect(":memory:")
        cursor = temp_database.cursor()
        cursor.execute(result)

    except sqlite3.Error as err:
        return err

    finally:
        if temp_database:
            cursor = temp_database.cursor()
            cursor.execute("drop table "+table_name[0]+" ;")
            cursor.close()

    return result