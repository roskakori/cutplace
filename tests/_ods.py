#!/usr/bin/env python
"""
Read and convert ODS files created by OpenOffice.org's Calc.
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

import argparse
import logging
import io
import sys

from cutplace import _compat
from cutplace import _tools
from cutplace import rowio

# TODO: Remove the whole module as it should be obsolete now due dev_torst.

_log = logging.getLogger('cutplace.ods')


def to_csv(ods_source_path, csv_target_path, dialect='excel', sheet=1):
    """
    Convert ODS file in `odsFilePath` to CSV using `dialect` and store the result in `csvTargetPath`.
    """
    assert ods_source_path is not None
    assert csv_target_path is not None
    assert dialect is not None
    assert sheet is not None
    assert sheet >= 1

    with io.open(csv_target_path, 'w', newline='', encoding='utf-8') as csv_target_file:
        csv_writer = _compat.csv_writer(csv_target_file, dialect)
        csv_writer.writerows(rowio.ods_rows(ods_source_path, sheet))


def _write_rst_row(rst_target_file, column_lengths, items):
    assert rst_target_file is not None
    assert column_lengths
    assert items
    assert len(column_lengths) >= len(items)

    for column_index in range(len(column_lengths)):
        column_length = column_lengths[column_index]
        if column_index < len(items):
            item = items[column_index]
        else:
            item = ""
        item_length = len(item)
        assert column_length >= item_length
        # FIXME: Add support for items containing line separators.
        if ("\n" in item) or ("\r" in item):
            raise NotImplementedError("item must not contain line separator: %r" % item)
        rst_target_file.write("+%s%s" % (item, " " * (column_length - item_length)))
    rst_target_file.write("+\n")


def _write_rst_separator_line(rst_target_file, column_lengths, line_separator):
    assert rst_target_file is not None
    assert column_lengths
    assert line_separator in ["-", "="]

    for column_length in column_lengths:
        rst_target_file.write("+")
        if column_length > 0:
            rst_target_file.write(line_separator * column_length)
    rst_target_file.write("+\n")


def to_rst(ods_source_path, rst_target_path, first_row_is_heading=True, sheet=1):
    """
    Convert ODS file in `odsFilePath` to reStructuredText and store the result in `rstTargetPath`.
    """
    assert ods_source_path is not None
    assert rst_target_path is not None
    assert sheet >= 1

    rows = list(rowio.ods_rows(ods_source_path, sheet))

    # Find out the length of each column.
    lengths = []
    is_first_row = True
    for row in rows:
        for column_index in range(len(row)):
            item = row[column_index]
            item_length = len(item)
            if is_first_row or (column_index == len(lengths)):
                lengths.append(item_length)
                is_first_row = False
            elif lengths[column_index] < item_length:
                lengths[column_index] = item_length

    if not lengths:
        raise ValueError("file must contain columns: \"%s\"" % ods_source_path)
    for column_index in range(len(lengths)):
        if lengths[column_index] == 0:
            raise ValueError("column %d in file %r must not always be empty" % (column_index + 1, ods_source_path))

    with io.open(rst_target_path, "w", encoding='utf-8') as rst_target_file:
        is_first_row = first_row_is_heading
        _write_rst_separator_line(rst_target_file, lengths, "-")
        for row in rows:
            _write_rst_row(rst_target_file, lengths, row)
            if is_first_row:
                line_separator = "="
                is_first_row = False
            else:
                line_separator = "-"
            _write_rst_separator_line(rst_target_file, lengths, line_separator)


# TODO: The handlers for the various formats should support items spawning multiple columns.
# TODO: Add support for items spawning multiple rows.
def main(arguments):
    assert arguments is not None

    _FORMAT_CSV = "csv"
    _FORMAT_RST = "rst"
    _FORMATS = [_FORMAT_CSV, _FORMAT_RST]
    _DEFAULT_FORMAT = _FORMAT_CSV
    _DEFAULT_SHEET = 1

    parser = argparse.ArgumentParser(description='convert ODS file to other formats')
    parser.add_argument(
        "-f", "--format", metavar="FORMAT", default=_DEFAULT_FORMAT, choices=sorted(_FORMATS), dest="format",
        help="target format: %s (default: %s)" % (_tools.human_readable_list(_FORMATS), _DEFAULT_FORMAT))
    parser.add_argument(
        "-1", "--heading", action="store_true", dest="firstRowIsHeading",
        help="render first row as heading")
    parser.add_argument(
        "-s", "--sheet", metavar="SHEET", default=_DEFAULT_SHEET, type=int, dest="sheet",
        help="sheet to convert (default: %d)" % _DEFAULT_SHEET)
    parser.add_argument('source_ods_path', metavar='ODS-FILE', help='the ODS file to convert')
    parser.add_argument('target_path', metavar='TARGET-FILE', nargs='?', help='the target file to write')
    args = parser.parse_args(arguments)

    # Additional command line argument validation.
    if args.sheet < 1:
        parser.error("option --sheet is %d but must be at least 1" % args.sheet)
    if (args.format == _FORMAT_CSV) and args.firstRowIsHeading:
        parser.error("option --heading can not be used with --format=csv")

    if args.target_path is None:
        assert args.format in _FORMATS
        suffix = '.' + args.format
        args.target_path = _tools.with_suffix(args.source_ods_path, suffix)

    _log.info("convert %r to %r using format %r", args.source_ods_path, args.target_path, args.format)
    try:
        if args.format == _FORMAT_CSV:
            to_csv(args.source_ods_path, args.target_path, sheet=args.sheet)
        elif args.format == _FORMAT_RST:
            to_rst(
                args.source_ods_path, args.target_path, first_row_is_heading=args.firstRowIsHeading, sheet=args.sheet)
        else:  # pragma: no cover
            raise NotImplementedError("format=%r" % args.format)
    except (EnvironmentError, OSError) as error:
        _log.error("cannot convert ods: %s", error)
        sys.exit(1)
    except Exception as error:
        _log.exception("cannot convert ods: %s", error)
        sys.exit(1)

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
