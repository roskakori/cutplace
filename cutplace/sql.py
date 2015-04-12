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
import six
import sqlite3

from cutplace import _tools
from cutplace import ranges
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


class AnsiSqlDialect():
    def __init__(self):
        keywords_as_list = [
            'absolute', 'action', 'add', 'after', 'all', 'allocate', 'alter', 'and', 'any', 'are', 'array', 'as', 'asc',
            'asensitive', 'assertion', 'asymmetric', 'at', 'atomic', 'authorization', 'avg', 'before', 'begin', 'between',
            'bigint', 'binary', 'bit', 'bit_length', 'blob', 'boolean', 'both', 'breadth', 'by', 'call', 'called',
            'cascade', 'cascaded', 'case', 'cast', 'catalog', 'char', 'character', 'character_length', 'char_length',
            'check', 'clob', 'close', 'coalesce', 'collate', 'collation', 'column', 'commit', 'condition', 'connect',
            'connection', 'constraint', 'constraints', 'constructor', 'contains', 'continue', 'convert', 'corresponding',
            'count', 'create', 'cross', 'cube', 'current', 'current_date', 'current_default_transform_group', 'current_path',
            'current_role', 'current_time', 'current_timestamp', 'current_transform_group_for_type', 'current_user',
            'cursor', 'cycle', 'data', 'date', 'day', 'deallocate', 'dec', 'decimal', 'declare', 'default', 'deferrable',
            'deferred', 'delete', 'depth', 'deref', 'desc', 'describe', 'descriptor', 'deterministic', 'diagnostics',
            'disconnect', 'distinct', 'do', 'domain', 'double', 'drop', 'dynamic', 'each', 'element', 'else', 'elseif',
            'end', 'equals', 'escape', 'except', 'exception', 'exec', 'execute', 'exists', 'exit', 'external', 'extract',
            'false', 'fetch', 'filter', 'first', 'float', 'for', 'foreign', 'found', 'free', 'from', 'full', 'function',
            'general', 'get', 'global', 'go', 'goto', 'grant', 'group', 'grouping', 'handler', 'having', 'hold', 'hour',
            'identity', 'if', 'immediate', 'in', 'indicator', 'initially', 'inner', 'inout', 'input', 'insensitive', 'insert',
            'int', 'integer', 'intersect', 'interval', 'into', 'is', 'isolation', 'iterate', 'join', 'key', 'language',
            'large', 'last', 'lateral', 'leading', 'leave', 'left', 'level', 'like', 'local', 'localtime', 'localtimestamp',
            'locator', 'loop', 'lower', 'map', 'match', 'max', 'member', 'merge', 'method', 'min', 'minute', 'modifies',
            'module', 'month', 'multiset', 'names', 'national', 'natural', 'nchar', 'nclob', 'new', 'next', 'no', 'none',
            'not', 'null', 'nullif', 'numeric', 'object', 'octet_length', 'of', 'old', 'on', 'only', 'open', 'option',
            'or', 'order', 'ordinality', 'out', 'outer', 'output', 'over', 'overlaps', 'pad', 'parameter', 'partial',
            'partition', 'path', 'position', 'precision', 'prepare', 'preserve', 'primary', 'prior', 'privileges',
            'procedure', 'public', 'range', 'read', 'reads', 'real', 'recursive', 'ref', 'references', 'referencing',
            'relative', 'release', 'repeat', 'resignal', 'restrict', 'result', 'return', 'returns', 'revoke', 'right',
            'role', 'rollback', 'rollup', 'routine', 'row', 'rows', 'savepoint', 'schema', 'scope', 'scroll', 'search',
            'second', 'section', 'select', 'sensitive', 'session', 'session_user', 'set', 'sets', 'signal', 'similar',
            'size', 'smallint', 'some', 'space', 'specific', 'specifictype', 'sql', 'sqlcode', 'sqlerror', 'sqlexception',
            'sqlstate', 'sqlwarning', 'start', 'state', 'static', 'submultiset', 'substring', 'sum', 'symmetric', 'system',
            'system_user', 'table', 'tablesample', 'temporary', 'then', 'time', 'timestamp', 'timezone_hour', 'timezone_minute',
            'to', 'trailing', 'transaction', 'translate', 'translation', 'treat', 'trigger', 'trim', 'true', 'under', 'undo',
            'union', 'unique', 'unknown', 'unnest', 'until', 'update', 'upper', 'usage', 'user', 'using', 'value', 'values',
            'varchar', 'varying', 'view', 'when', 'whenever', 'where', 'while', 'window', 'with', 'within', 'without',
            'work', 'write', 'year', 'zone']

        self._keywords = set(keywords_as_list)

    @property
    def keywords(self):
        return self._keywords

    def sql_type(self, sql_ansi_type):
        """Same kind of tuple as with py:meth`fields.AbstractFieldFormat.sql_ansi_type().`"""
        return sql_ansi_type

    def sql_escaped(self, text):
        # TODO: Escape characters < 32.
        return "'" + text.replace("'", "''") + "'"

    def is_keyword(self, word):
        assert word is not None
        return word.lower() in self.keywords


class OracleSqlDialect(AnsiSqlDialect):

    def __init__(self):
        keywords_as_list = [
            'a', 'add', 'agent', 'aggregate', 'all', 'alter', 'and', 'any', 'array', 'arrow', 'as',
            'asc', 'at', 'attribute', 'authid', 'avg', 'begin', 'between', 'bfile_base', 'binary', 'blob_base', 'block',
            'body', 'both', 'bound', 'bulk', 'by', 'byte', 'c', 'call', 'calling', 'cascade', 'case', 'char', 'character',
            'charset', 'charsetform', 'charsetid', 'char_base', 'check', 'clob_base', 'close', 'cluster', 'clusters',
            'colauth', 'collect', 'columns', 'comment', 'commit', 'committed', 'compiled', 'compress', 'connect', 'constant',
            'constructor', 'context', 'convert', 'count', 'crash', 'create', 'current', 'cursor', 'customdatum', 'dangling',
            'data', 'date', 'date_base', 'day', 'decimal', 'declare', 'default', 'define', 'delete', 'desc', 'deterministic',
            'distinct', 'double', 'drop', 'duration', 'element', 'else', 'elsif', 'empty', 'end', 'escape', 'except',
            'exception', 'exceptions', 'exclusive', 'execute', 'exists', 'exit', 'external', 'fetch', 'final', 'fixed',
            'float', 'for', 'forall', 'force', 'form', 'from', 'function', 'general', 'goto', 'grant', 'group', 'hash',
            'having', 'heap', 'hidden', 'hour', 'identified', 'if', 'immediate', 'in', 'including', 'index', 'indexes',
            'indicator', 'indices', 'infinite', 'insert', 'instantiable', 'int', 'interface', 'intersect', 'interval',
            'into', 'invalidate', 'is', 'isolation', 'java', 'language', 'large', 'leading', 'length', 'level', 'library',
            'like', 'like2', 'like4', 'likec', 'limit', 'limited', 'local', 'lock', 'long', 'loop', 'map', 'max', 'maxlen',
            'member', 'merge', 'min', 'minus', 'minute', 'mod', 'mode', 'modify', 'month', 'multiset', 'name', 'nan',
            'national', 'native', 'nchar', 'new', 'nocompress', 'nocopy', 'not', 'nowait', 'null', 'number_base', 'object',
            'ocicoll', 'ocidate', 'ocidatetime', 'ociduration', 'ociinterval', 'ociloblocator', 'ocinumber', 'ociraw',
            'ociref', 'ocirefcursor', 'ocirowid', 'ocistring', 'ocitype', 'of', 'on', 'only', 'opaque', 'open', 'operator',
            'option', 'or', 'oracle', 'oradata', 'order,overlaps', 'organization', 'orlany', 'orlvary', 'others', 'out',
            'overriding', 'package', 'parallel_enable', 'parameter', 'parameters', 'partition', 'pascal', 'pipe',
            'pipelined', 'pragma', 'precision', 'prior', 'private', 'procedure', 'public', 'raise', 'range', 'raw', 'read',
            'record', 'ref', 'reference', 'rem', 'remainder', 'rename', 'resource', 'result', 'return', 'returning',
            'reverse', 'revoke', 'rollback', 'row', 'sample', 'save', 'savepoint', 'sb1', 'sb2', 'sb4', 'second', 'segment',
            'select', 'self', 'separate', 'sequence', 'serializable', 'set', 'share', 'short', 'size', 'size_t', 'some',
            'sparse', 'sql', 'sqlcode', 'sqldata', 'sqlname', 'sqlstate', 'standard', 'start', 'static', 'stddev', 'stored',
            'string', 'struct', 'style', 'submultiset', 'subpartition', 'substitutable', 'subtype', 'sum', 'synonym',
            'tabauth', 'table', 'tdo', 'the', 'then', 'time', 'timestamp', 'timezone_abbr', 'timezone_hour', 'timezone_minute',
            'timezone_region', 'to', 'trailing', 'transac', 'transactional', 'trusted', 'type', 'ub1', 'ub2', 'ub4', 'under',
            'union', 'unique', 'unsigned', 'untrusted', 'update', 'use', 'using', 'valist', 'value', 'values', 'variable',
            'variance', 'varray', 'varying', 'view', 'views', 'void', 'when', 'where', 'while', 'with', 'work', 'wrapped',
            'write', 'year', 'zone']

        self._keywords = set(keywords_as_list)

    def sql_type(self, sql_ansi_type):
        ansi_type = sql_ansi_type[0]
        result = sql_ansi_type

        if ansi_type == 'decimal':
            oracle_type = 'number'
            _, scale, precision = sql_ansi_type
            result = (oracle_type, scale, precision)

        elif ansi_type == 'varchar':
            oracle_type = 'varchar2'
            length = sql_ansi_type[1]
            result = (oracle_type, length)

        elif ansi_type == 'int':
            length = sql_ansi_type[1]
            if length > 31:
                result = ('number', length, 0)

        return result


class MSSqlDialect(AnsiSqlDialect):

    def __init__(self):
        keywords = [
            'add', 'all', 'alter', 'and', 'any', 'as', 'asc', 'authorization', 'backup', 'begin', 'between', 'break',
            'browse', 'bulk', 'by', 'cascade', 'case', 'check', 'checkpoint', 'close', 'clustered', 'coalesce', 'collate',
            'column', 'commit', 'compute', 'constraint', 'contains', 'containstable', 'continue', 'convert', 'create',
            'cross', 'current', 'current_date', 'current_time', 'current_timestamp', 'current_user', 'cursor', 'database',
            'dbcc', 'deallocate', 'declare', 'default', 'delete', 'deny', 'desc', 'disk', 'distinct', 'distributed',
            'double', 'drop', 'dump', 'else', 'end', 'errlvl', 'escape', 'except', 'exec', 'execute', 'exists', 'exit',
            'external', 'fetch', 'file', 'fillfactor', 'for', 'foreign', 'freetext', 'freetexttable', 'from', 'full',
            'function', 'goto', 'grant', 'group', 'having', 'holdlock', 'identity', 'identitycol', 'identity_insert',
            'if', 'in', 'index', 'inner', 'insert', 'intersect', 'into', 'is', 'join', 'key', 'kill', 'left', 'like',
            'lineno', 'load', 'merge', 'national', 'nocheck', 'nonclustered', 'not', 'null', 'nullif', 'of', 'off',
            'offsets', 'on', 'open', 'opendatasource', 'openquery', 'openrowset', 'openxml', 'option', 'or', 'order',
            'outer', 'over', 'percent', 'pivot', 'plan', 'precision', 'primary', 'print', 'proc', 'procedure', 'public',
            'raiserror', 'read', 'readtext', 'reconfigure', 'references', 'replication', 'restore', 'restrict', 'return',
            'revert', 'revoke', 'right', 'rollback', 'rowcount', 'rowguidcol', 'rule', 'save', 'schema', 'securityaudit',
            'select', 'semantickeyphrasetable', 'semanticsimilaritydetailstable', 'semanticsimilaritytable', 'session_user',
            'set', 'setuser', 'shutdown', 'some', 'statistics', 'system_user', 'table', 'tablesample', 'textsize', 'then',
            'to', 'top', 'tran', 'transaction', 'trigger', 'truncate', 'try_convert', 'tsequal', 'union', 'unique', 'unpivot',
            'update', 'updatetext', 'use', 'user', 'values', 'varying', 'view', 'waitfor', 'when', 'where', 'while', 'with',
            'withingroup', 'writetext']

        self._keywords = set(keywords)

    def sql_type(self, sql_ansi_type):
        ansi_type = sql_ansi_type[0]
        result = sql_ansi_type

        if ansi_type == 'int':
            length = sql_ansi_type[1]

            if length <= 15:
                result = ('smallint', length)
            elif length <= 31:
                result = ('int', length)
            elif length <= 63:
                result = ('bigint', length)
            else:
                result = ('decimal', length, 0)

        return result


ANSI_SQL_DIALECT = AnsiSqlDialect()


def assert_is_valid_dialect(dialect):
    assert dialect in (ANSI, DB2, MSSQL, MYSQL, ORACLE), 'dialect=%r' % dialect


def write_create(cid_path, cid_reader):
    #TODO: add option for different cid types
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
