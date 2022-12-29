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
import io
import logging
import os.path

from cutplace import rowio

# TODO: Move to module ``ranges``.
MAX_TINYINT = 2**8 - 1  # NOTE: Tinyint really is unsigned.
MAX_SMALLINT = 2**15 - 1
MAX_INTEGER = 2**31 - 1
MAX_BIGINT = 2**63 - 1

#: SQL dialect name: ANSI SQL
ANSI = "ANSI"
#: SQL dialect name: DB2 used by IBM
DB2 = "DB2"
#: SQL dialect name: Transact-SQL used by Microsoft SQL and Sybase
TRANSACT = "Transact-SQL"
#: SQL dialect name: PL/SQL used by Oracle
PL = "PL/SQL"

_INT_TYPES = set(["bigint", "int", "smallint", "tinyint"])

_log = logging.getLogger("cutplace")


class AnsiSqlDialect:
    """
    ANSI SQL dialect basically but not really supported by several database vendors.
    """

    def __init__(self):
        keywords_as_list = [
            "absolute",
            "action",
            "add",
            "after",
            "all",
            "allocate",
            "alter",
            "and",
            "any",
            "are",
            "array",
            "as",
            "asc",
            "asensitive",
            "assertion",
            "asymmetric",
            "at",
            "atomic",
            "authorization",
            "avg",
            "before",
            "begin",
            "between",
            "bigint",
            "binary",
            "bit",
            "bit_length",
            "blob",
            "boolean",
            "both",
            "breadth",
            "by",
            "call",
            "called",
            "cascade",
            "cascaded",
            "case",
            "cast",
            "catalog",
            "char",
            "character",
            "character_length",
            "char_length",
            "check",
            "clob",
            "close",
            "coalesce",
            "collate",
            "collation",
            "column",
            "commit",
            "condition",
            "connect",
            "connection",
            "constraint",
            "constraints",
            "constructor",
            "contains",
            "continue",
            "convert",
            "corresponding",
            "count",
            "create",
            "cross",
            "cube",
            "current",
            "current_date",
            "current_default_transform_group",
            "current_path",
            "current_role",
            "current_time",
            "current_timestamp",
            "current_transform_group_for_type",
            "current_user",
            "cursor",
            "cycle",
            "data",
            "date",
            "day",
            "deallocate",
            "dec",
            "decimal",
            "declare",
            "default",
            "deferrable",
            "deferred",
            "delete",
            "depth",
            "deref",
            "desc",
            "describe",
            "descriptor",
            "deterministic",
            "diagnostics",
            "disconnect",
            "distinct",
            "do",
            "domain",
            "double",
            "drop",
            "dynamic",
            "each",
            "element",
            "else",
            "elseif",
            "end",
            "equals",
            "escape",
            "except",
            "exception",
            "exec",
            "execute",
            "exists",
            "exit",
            "external",
            "extract",
            "false",
            "fetch",
            "filter",
            "first",
            "float",
            "for",
            "foreign",
            "found",
            "free",
            "from",
            "full",
            "function",
            "general",
            "get",
            "global",
            "go",
            "goto",
            "grant",
            "group",
            "grouping",
            "handler",
            "having",
            "hold",
            "hour",
            "identity",
            "if",
            "immediate",
            "in",
            "indicator",
            "initially",
            "inner",
            "inout",
            "input",
            "insensitive",
            "insert",
            "int",
            "integer",
            "intersect",
            "interval",
            "into",
            "is",
            "isolation",
            "iterate",
            "join",
            "key",
            "language",
            "large",
            "last",
            "lateral",
            "leading",
            "leave",
            "left",
            "level",
            "like",
            "local",
            "localtime",
            "localtimestamp",
            "locator",
            "loop",
            "lower",
            "map",
            "match",
            "max",
            "member",
            "merge",
            "method",
            "min",
            "minute",
            "modifies",
            "module",
            "month",
            "multiset",
            "names",
            "national",
            "natural",
            "nchar",
            "nclob",
            "new",
            "next",
            "no",
            "none",
            "not",
            "null",
            "nullif",
            "numeric",
            "object",
            "octet_length",
            "of",
            "old",
            "on",
            "only",
            "open",
            "option",
            "or",
            "order",
            "ordinality",
            "out",
            "outer",
            "output",
            "over",
            "overlaps",
            "pad",
            "parameter",
            "partial",
            "partition",
            "path",
            "position",
            "precision",
            "prepare",
            "preserve",
            "primary",
            "prior",
            "privileges",
            "procedure",
            "public",
            "range",
            "read",
            "reads",
            "real",
            "recursive",
            "ref",
            "references",
            "referencing",
            "relative",
            "release",
            "repeat",
            "resignal",
            "restrict",
            "result",
            "return",
            "returns",
            "revoke",
            "right",
            "role",
            "rollback",
            "rollup",
            "routine",
            "row",
            "rows",
            "savepoint",
            "schema",
            "scope",
            "scroll",
            "search",
            "second",
            "section",
            "select",
            "sensitive",
            "session",
            "session_user",
            "set",
            "sets",
            "signal",
            "similar",
            "size",
            "smallint",
            "some",
            "space",
            "specific",
            "specifictype",
            "sql",
            "sqlcode",
            "sqlerror",
            "sqlexception",
            "sqlstate",
            "sqlwarning",
            "start",
            "state",
            "static",
            "submultiset",
            "substring",
            "sum",
            "symmetric",
            "system",
            "system_user",
            "table",
            "tablesample",
            "temporary",
            "then",
            "time",
            "timestamp",
            "timezone_hour",
            "timezone_minute",
            "to",
            "trailing",
            "transaction",
            "translate",
            "translation",
            "treat",
            "trigger",
            "trim",
            "true",
            "under",
            "undo",
            "union",
            "unique",
            "unknown",
            "unnest",
            "until",
            "update",
            "upper",
            "usage",
            "user",
            "using",
            "value",
            "values",
            "varchar",
            "varying",
            "view",
            "when",
            "whenever",
            "where",
            "while",
            "window",
            "with",
            "within",
            "without",
            "work",
            "write",
            "year",
            "zone",
        ]
        self._keywords = set(keywords_as_list)

    @property
    def keywords(self):
        return self._keywords

    def sql_type(self, sql_ansi_type):
        """
        Same kind of tuple as with :py:meth:`fields.AbstractFieldFormat.sql_ansi_type().`
        """
        assert_is_valid_ansi_type(sql_ansi_type)
        return sql_ansi_type

    def sql_string_escaped(self, text):
        assert text is not None
        # TODO: Escape characters < 32.
        return "'" + text.replace("'", "''") + "'"

    def is_keyword(self, word):
        assert word is not None
        return word.lower() in self.keywords

    def __str__(self):
        return ANSI


class PlSqlDialect(AnsiSqlDialect):
    """
    PL/SQL dialect used by Oracle.
    """

    def __init__(self):
        keywords_as_list = [
            "a",
            "add",
            "agent",
            "aggregate",
            "all",
            "alter",
            "and",
            "any",
            "array",
            "arrow",
            "as",
            "asc",
            "at",
            "attribute",
            "authid",
            "avg",
            "begin",
            "between",
            "bfile_base",
            "binary",
            "blob_base",
            "block",
            "body",
            "both",
            "bound",
            "bulk",
            "by",
            "byte",
            "c",
            "call",
            "calling",
            "cascade",
            "case",
            "char",
            "character",
            "charset",
            "charsetform",
            "charsetid",
            "char_base",
            "check",
            "clob_base",
            "close",
            "cluster",
            "clusters",
            "colauth",
            "collect",
            "columns",
            "comment",
            "commit",
            "committed",
            "compiled",
            "compress",
            "connect",
            "constant",
            "constructor",
            "context",
            "convert",
            "count",
            "crash",
            "create",
            "current",
            "cursor",
            "customdatum",
            "dangling",
            "data",
            "date",
            "date_base",
            "day",
            "decimal",
            "declare",
            "default",
            "define",
            "delete",
            "desc",
            "deterministic",
            "distinct",
            "double",
            "drop",
            "duration",
            "element",
            "else",
            "elsif",
            "empty",
            "end",
            "escape",
            "except",
            "exception",
            "exceptions",
            "exclusive",
            "execute",
            "exists",
            "exit",
            "external",
            "fetch",
            "final",
            "fixed",
            "float",
            "for",
            "forall",
            "force",
            "form",
            "from",
            "function",
            "general",
            "goto",
            "grant",
            "group",
            "hash",
            "having",
            "heap",
            "hidden",
            "hour",
            "identified",
            "if",
            "immediate",
            "in",
            "including",
            "index",
            "indexes",
            "indicator",
            "indices",
            "infinite",
            "insert",
            "instantiable",
            "int",
            "interface",
            "intersect",
            "interval",
            "into",
            "invalidate",
            "is",
            "isolation",
            "java",
            "language",
            "large",
            "leading",
            "length",
            "level",
            "library",
            "like",
            "like2",
            "like4",
            "likec",
            "limit",
            "limited",
            "local",
            "lock",
            "long",
            "loop",
            "map",
            "max",
            "maxlen",
            "member",
            "merge",
            "min",
            "minus",
            "minute",
            "mod",
            "mode",
            "modify",
            "month",
            "multiset",
            "name",
            "nan",
            "national",
            "native",
            "nchar",
            "new",
            "nocompress",
            "nocopy",
            "not",
            "nowait",
            "null",
            "number_base",
            "object",
            "ocicoll",
            "ocidate",
            "ocidatetime",
            "ociduration",
            "ociinterval",
            "ociloblocator",
            "ocinumber",
            "ociraw",
            "ociref",
            "ocirefcursor",
            "ocirowid",
            "ocistring",
            "ocitype",
            "of",
            "on",
            "only",
            "opaque",
            "open",
            "operator",
            "option",
            "or",
            "oracle",
            "oradata",
            "order,overlaps",
            "organization",
            "orlany",
            "orlvary",
            "others",
            "out",
            "overriding",
            "package",
            "parallel_enable",
            "parameter",
            "parameters",
            "partition",
            "pascal",
            "pipe",
            "pipelined",
            "pragma",
            "precision",
            "prior",
            "private",
            "procedure",
            "public",
            "raise",
            "range",
            "raw",
            "read",
            "record",
            "ref",
            "reference",
            "rem",
            "remainder",
            "rename",
            "resource",
            "result",
            "return",
            "returning",
            "reverse",
            "revoke",
            "rollback",
            "row",
            "sample",
            "save",
            "savepoint",
            "sb1",
            "sb2",
            "sb4",
            "second",
            "segment",
            "select",
            "self",
            "separate",
            "sequence",
            "serializable",
            "set",
            "share",
            "short",
            "size",
            "size_t",
            "some",
            "sparse",
            "sql",
            "sqlcode",
            "sqldata",
            "sqlname",
            "sqlstate",
            "standard",
            "start",
            "static",
            "stddev",
            "stored",
            "string",
            "struct",
            "style",
            "submultiset",
            "subpartition",
            "substitutable",
            "subtype",
            "sum",
            "synonym",
            "tabauth",
            "table",
            "tdo",
            "the",
            "then",
            "time",
            "timestamp",
            "timezone_abbr",
            "timezone_hour",
            "timezone_minute",
            "timezone_region",
            "to",
            "trailing",
            "transac",
            "transactional",
            "trusted",
            "type",
            "ub1",
            "ub2",
            "ub4",
            "under",
            "union",
            "unique",
            "unsigned",
            "untrusted",
            "update",
            "use",
            "using",
            "valist",
            "value",
            "values",
            "variable",
            "variance",
            "varray",
            "varying",
            "view",
            "views",
            "void",
            "when",
            "where",
            "while",
            "with",
            "work",
            "wrapped",
            "write",
            "year",
            "zone",
        ]
        self._keywords = set(keywords_as_list)

    def sql_type(self, sql_ansi_type):
        ansi_type = sql_ansi_type[0]
        result = sql_ansi_type

        if ansi_type == "decimal":
            oracle_type = "number"
            _, scale, precision = sql_ansi_type
            result = (oracle_type, scale, precision)

        elif ansi_type == "varchar":
            oracle_type = "varchar2"
            length = sql_ansi_type[1]
            result = (oracle_type, length)

        elif ansi_type == "int":
            length = sql_ansi_type[1]
            if length > MAX_INTEGER:
                result = ("number", length, 0)

        return result

    def __str__(self):
        return PL


class TransactSqlDialect(AnsiSqlDialect):
    """
    Transact-SQL dialect used by Microsoft SQL Server and Sybase.
    """

    def __init__(self):
        keywords = [
            "add",
            "all",
            "alter",
            "and",
            "any",
            "as",
            "asc",
            "authorization",
            "backup",
            "begin",
            "between",
            "break",
            "browse",
            "bulk",
            "by",
            "cascade",
            "case",
            "check",
            "checkpoint",
            "close",
            "clustered",
            "coalesce",
            "collate",
            "column",
            "commit",
            "compute",
            "constraint",
            "contains",
            "containstable",
            "continue",
            "convert",
            "create",
            "cross",
            "current",
            "current_date",
            "current_time",
            "current_timestamp",
            "current_user",
            "cursor",
            "database",
            "dbcc",
            "deallocate",
            "declare",
            "default",
            "delete",
            "deny",
            "desc",
            "disk",
            "distinct",
            "distributed",
            "double",
            "drop",
            "dump",
            "else",
            "end",
            "errlvl",
            "escape",
            "except",
            "exec",
            "execute",
            "exists",
            "exit",
            "external",
            "fetch",
            "file",
            "fillfactor",
            "for",
            "foreign",
            "freetext",
            "freetexttable",
            "from",
            "full",
            "function",
            "goto",
            "grant",
            "group",
            "having",
            "holdlock",
            "identity",
            "identitycol",
            "identity_insert",
            "if",
            "in",
            "index",
            "inner",
            "insert",
            "intersect",
            "into",
            "is",
            "join",
            "key",
            "kill",
            "left",
            "like",
            "lineno",
            "load",
            "merge",
            "national",
            "nocheck",
            "nonclustered",
            "not",
            "null",
            "nullif",
            "of",
            "off",
            "offsets",
            "on",
            "open",
            "opendatasource",
            "openquery",
            "openrowset",
            "openxml",
            "option",
            "or",
            "order",
            "outer",
            "over",
            "percent",
            "pivot",
            "plan",
            "precision",
            "primary",
            "print",
            "proc",
            "procedure",
            "public",
            "raiserror",
            "read",
            "readtext",
            "reconfigure",
            "references",
            "replication",
            "restore",
            "restrict",
            "return",
            "revert",
            "revoke",
            "right",
            "rollback",
            "rowcount",
            "rowguidcol",
            "rule",
            "save",
            "schema",
            "securityaudit",
            "select",
            "semantickeyphrasetable",
            "semanticsimilaritydetailstable",
            "semanticsimilaritytable",
            "session_user",
            "set",
            "setuser",
            "shutdown",
            "some",
            "statistics",
            "system_user",
            "table",
            "tablesample",
            "textsize",
            "then",
            "to",
            "top",
            "tran",
            "transaction",
            "trigger",
            "truncate",
            "try_convert",
            "tsequal",
            "union",
            "unique",
            "unpivot",
            "update",
            "updatetext",
            "use",
            "user",
            "values",
            "varying",
            "view",
            "waitfor",
            "when",
            "where",
            "while",
            "with",
            "withingroup",
            "writetext",
        ]
        self._keywords = set(keywords)

    def sql_type(self, sql_ansi_type):
        ansi_type = sql_ansi_type[0]
        if ansi_type == "int":
            limit = sql_ansi_type[1]
            assert limit >= 0, "length=%r" % limit

            if limit <= MAX_TINYINT:
                result = ("tinyint", limit)
            elif limit <= MAX_SMALLINT:
                result = ("smallint", limit)
            elif limit <= MAX_INTEGER or limit is None:
                result = ("int", limit)
            elif limit <= MAX_BIGINT:
                result = ("bigint", limit)
            else:
                result = ("decimal", limit, 0)
        else:
            result = sql_ansi_type

        return result

    def __str__(self):
        return TRANSACT


class Db2SqlDialect(AnsiSqlDialect):
    """
    SQL dialect used by IBM DB2.
    """

    def __init__(self):
        keywords = [
            "add",
            "after",
            "all",
            "allocate",
            "allow",
            "alter",
            "and",
            "any",
            "as",
            "asensitive",
            "associate",
            "asutime",
            "at",
            "audit",
            "aux",
            "auxiliary",
            "before",
            "begin",
            "between",
            "bufferpool",
            "by",
            "call",
            "capture",
            "cascaded",
            "case",
            "cast",
            "ccsid",
            "char",
            "character",
            "check",
            "clone",
            "close",
            "cluster",
            "collection",
            "collid",
            "column",
            "comment",
            "commit",
            "concat",
            "condition",
            "connect",
            "connection",
            "constraint",
            "contains",
            "content",
            "continue",
            "create",
            "current",
            "current_date",
            "current_lc_ctype",
            "current_path",
            "current_schema",
            "current_time",
            "current_timestamp",
            "currval1",
            "cursor",
            "data",
            "database",
            "day",
            "days",
            "dbinfo",
            "declare",
            "default",
            "delete",
            "descriptor",
            "deterministic",
            "disable",
            "disallow",
            "distinct",
            "do",
            "document",
            "double",
            "drop",
            "dssize",
            "dynamic",
            "editproc",
            "else",
            "elseif",
            "encoding",
            "encryption",
            "end",
            "end-exec2",
            "ending",
            "erase",
            "escape",
            "except",
            "exception",
            "execute",
            "exists",
            "exit",
            "explain",
            "external",
            "fenced",
            "fetch",
            "fieldproc",
            "final",
            "first1",
            "for",
            "free",
            "from",
            "full",
            "function",
            "generated",
            "get",
            "global",
            "go",
            "goto",
            "grant",
            "group",
            "handler",
            "having",
            "hold",
            "hour",
            "hours",
            "if",
            "immediate",
            "in",
            "inclusive",
            "index",
            "inherit",
            "inner",
            "inout",
            "insensitive",
            "insert",
            "intersect",
            "into",
            "is",
            "isobid",
            "iterate",
            "jar",
            "join",
            "keep",
            "key",
            "label",
            "language",
            "last1",
            "lc_ctype",
            "leave",
            "left",
            "like",
            "local",
            "locale",
            "locator",
            "locators",
            "lock",
            "lockmax",
            "locksize",
            "long",
            "loop",
            "maintained",
            "materialized",
            "microsecond",
            "microseconds",
            "minute",
            "minutes",
            "modifies",
            "month",
            "months",
            "next1",
            "nextval",
            "no",
            "none",
            "not",
            "null",
            "nulls",
            "numparts",
            "obid",
            "of",
            "old1",
            "on",
            "open",
            "optimization",
            "optimize",
            "or",
            "order",
            "organization1",
            "out",
            "outer",
            "package",
            "padded",
            "parameter",
            "part",
            "partition",
            "partitioned",
            "partitioning",
            "path",
            "period1",
            "piecesize",
            "plan",
            "precision",
            "prepare",
            "prevval",
            "prior1",
            "priqty",
            "privileges",
            "procedure",
            "program",
            "psid",
            "public",
            "query",
            "queryno",
            "reads",
            "references",
            "refresh",
            "release",
            "rename",
            "repeat",
            "resignal",
            "restrict",
            "result",
            "result_set_locator",
            "return",
            "returns",
            "revoke",
            "right",
            "role",
            "rollback",
            "round_ceiling",
            "round_down",
            "round_floor",
            "round_half_down",
            "round_half_even",
            "round_half_up",
            "round_up",
            "row",
            "rowset",
            "run",
            "savepoint",
            "schema",
            "scratchpad",
            "second",
            "seconds",
            "secqty",
            "security",
            "select",
            "sensitive",
            "sequence",
            "session_user",
            "set",
            "signal",
            "simple",
            "some",
            "source",
            "specific",
            "standard",
            "statement",
            "static",
            "stay",
            "stogroup",
            "stores",
            "style",
            "summary",
            "synonym",
            "sysdate1",
            "system",
            "systimestamp1",
            "table",
            "tablespace",
            "then",
            "to",
            "trigger",
            "truncate",
            "type",
            "undo",
            "union",
            "unique",
            "until",
            "update",
            "user",
            "using",
            "validproc",
            "value",
            "values",
            "variable",
            "variant",
            "vcat",
            "view",
            "volatile",
            "volumes",
            "when",
            "whenever",
            "where",
            "while",
            "with",
            "wlm",
            "xmlcast",
            "xmlexists",
            "xmlnamespaces",
            "year",
            "years",
            "zone",
        ]
        self._keywords = set(keywords)

    def sql_type(self, sql_ansi_type):
        ansi_type = sql_ansi_type[0]
        result = sql_ansi_type
        if ansi_type == "int":
            length = sql_ansi_type[1]
            if length <= MAX_SMALLINT:
                result = ("smallint", length)
            elif length <= MAX_INTEGER or length is None:
                result = ("integer", length)
            elif length <= MAX_BIGINT:
                result = ("bigint", length)
            else:
                result = ("decimal", length)
        return result

    def __str__(self):
        return DB2


ANSI_SQL_DIALECT = AnsiSqlDialect()
DB2_SQL_DIALECT = Db2SqlDialect()
TRANSACT_SQL_DIALECT = TransactSqlDialect()
PL_SQL_DIALECT = PlSqlDialect()

#: Mapping of names to SQL dialects.
SQL_NAME_TO_DIALECT_MAP = {
    ANSI: ANSI_SQL_DIALECT,
    DB2: DB2_SQL_DIALECT,
    TRANSACT: TRANSACT_SQL_DIALECT,
    PL: PL_SQL_DIALECT,
}

_VALID_ANSI_TYPE_NAMES = ("char", "date", "decimal", "int", "varchar")


def assert_is_valid_dialect(dialect):
    assert str(dialect) in (ANSI, DB2, TRANSACT, PL), "dialect=%r" % dialect


def assert_is_valid_ansi_type(ansi_type):
    """
    Assert that ``ansi_type`` conforms to the format described at
    :py:meth:`fields.AbstractFieldFormat.sql_ansi_type().`
    """
    assert ansi_type is not None
    assert isinstance(ansi_type, tuple), "type(ansi_type) must be a tuple but is: %s" % type(ansi_type)
    ansi_type_items = list(ansi_type)
    while (len(ansi_type_items) >= 2) and (ansi_type_items[-1] is None):
        del ansi_type_items[-1]
    tuple_count = len(ansi_type_items)
    assert tuple_count >= 1
    type_name = ansi_type[0]
    if type_name in ("char", "varchar"):
        assert tuple_count <= 2, "ansi_type=%s" % (ansi_type,)
    elif type_name == "date":
        assert tuple_count == 1
    elif type_name == "decimal":
        assert tuple_count <= 3
    elif type_name == "int":
        assert tuple_count <= 2
    else:
        assert False, "ansi_type.name=%r but must be one of %s" % (type_name, _VALID_ANSI_TYPE_NAMES)
    for ansi_type_index, ansi_type_item in enumerate(ansi_type_items[1:], 1):
        if ansi_type_item is not None:
            assert isinstance(ansi_type_item, int), "type(ansi_type[%d]) must be int but is %s" % (
                ansi_type_index,
                type(ansi_type[ansi_type_index]),
            )
            assert ansi_type_item >= 0, "ansi_type[%d] = %d must be at least 0" % (ansi_type_index, ansi_type_item)


def write_create(cid_path, cid_reader):
    # TODO: Add option for different cid types.
    cid_reader.read(cid_path, rowio.excel_rows(cid_path))

    create_path = os.path.splitext(cid_path)[0] + "_create.sql"
    # TODO: Add option to specify target folder for SQL files.
    _log.info('write SQL create statements to "%s"', create_path)
    with io.open(create_path, "w", encoding="utf-8") as create_file:
        # TODO: Add option for encoding.
        table = os.path.splitext(os.path.basename(cid_path))[0]
        sql_factory = SqlFactory(cid_reader, table)
        create_file.write(sql_factory.create_table_statement())
        # TODO: Add option for target SQL dialect


class SqlFactory(object):
    def __init__(self, cid, table, dialect=ANSI_SQL_DIALECT):
        self._cid = cid
        self._table = table
        self._dialect = dialect
        # TODO: Add option to set SQL indent.
        self._indent = "    "

        assert_is_valid_dialect(self._dialect)

    @property
    def cid(self):
        return self._cid

    def sql_fields(self):
        """
        Tuples `(field_name, field_type, length, precision, is_not_null, default_value)`
        """
        for field in self._cid.field_formats:
            assert_is_valid_ansi_type(field.sql_ansi_type())
            sql_type, sql_length, sql_precision = (field.sql_ansi_type() + (None, None))[:3]
            sql_type, sql_length, sql_precision = (
                self._dialect.sql_type((sql_type, sql_length, sql_precision)) + (None, None)
            )[:3]
            field_name = field.field_name
            if self._dialect.is_keyword(field_name):
                field_name = '"' + field_name + '"'
            row = (field_name, sql_type, sql_length, sql_precision, field.is_allowed_to_be_empty, field.empty_value)
            yield row

    def create_table_statement(self):
        result = "create table " + self._table + " (\n"
        first_field = True

        # get column definitions for all fields
        for field_name, field_type, length, precision, is_not_null, default_value in self.sql_fields():
            if not first_field:
                result += ",\n"

            column_def = self._indent + field_name + " " + field_type
            if field_type not in _INT_TYPES:
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

        result += "\n);"

        return result

    def create_index_statements(self):
        pass

    def create_constraint_statements(self):
        pass
