#!/usr/bin/env python
"""
Read and convert ODS files created by OpenOffice.org's Calc.
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

import argparse
import csv
import logging
import io
import sys

from . import _tools

_log = logging.getLogger("cutplace.ods")


def toCsv(odsFilePath, csvTargetPath, dialect="excel", sheet=1):
    """
    Convert ODS file in `odsFilePath` to CSV using `dialect` and store the result in `csvTargetPath`.
    """
    assert odsFilePath is not None
    assert csvTargetPath is not None
    assert dialect is not None
    assert sheet is not None
    assert sheet >= 1

    with io.open(csvTargetPath, 'w', encoding='utf-8') as csvTargetFile:
        csvWriter = csv.writer(csvTargetFile, dialect)
        csvWriter.writerows(_tools.ods_rows(odsFilePath, sheet))


def _writeRstRow(rstTargetFile, columnLengths, items):
    assert rstTargetFile is not None
    assert columnLengths
    assert items
    assert len(columnLengths) >= len(items)

    for columnIndex in range(len(columnLengths)):
        columnLength = columnLengths[columnIndex]
        if columnIndex < len(items):
            item = items[columnIndex]
        else:
            item = ""
        itemLength = len(item)
        assert columnLength >= itemLength
        # FIXME: Add support for items containing line separators.
        if ("\n" in item) or ("\r" in item):
            raise NotImplementedError("item must not contain line separator: %r" % item)
        rstTargetFile.write("+%s%s" % (item, " " * (columnLength - itemLength)))
    rstTargetFile.write("+\n")


def _writeRstSeparatorLine(rstTargetFile, columnLengths, lineSeparator):
    assert rstTargetFile is not None
    assert columnLengths
    assert lineSeparator in ["-", "="]

    for columnLength in columnLengths:
        rstTargetFile.write("+")
        if columnLength > 0:
            rstTargetFile.write(lineSeparator * columnLength)
    rstTargetFile.write("+\n")


def toRst(odsFilePath, rstTargetPath, firstRowIsHeading=True, sheet=1):
    """
    Convert ODS file in `odsFilePath` to reStructuredText and store the result in `rstTargetPath`.
    """
    assert odsFilePath is not None
    assert rstTargetPath is not None
    assert sheet >= 1

    rows = list(_tools.ods_rows(odsFilePath, sheet))

    # Find out the length of each column.
    lengths = []
    isFirstRow = True
    for row in rows:
        for columnIndex in range(len(row)):
            item = row[columnIndex]
            itemLength = len(item)
            if isFirstRow or (columnIndex == len(lengths)):
                lengths.append(itemLength)
                isFirstRow = False
            elif lengths[columnIndex] < itemLength:
                lengths[columnIndex] = itemLength

    if not lengths:
        raise ValueError("file must contain columns: \"%s\"" % odsFilePath)
    for columnIndex in range(len(lengths)):
        if lengths[columnIndex] == 0:
            raise ValueError("column %d in file %r must not always be empty" % (columnIndex + 1, odsFilePath))

    with io.open(rstTargetPath, "w", encoding='utf-8') as rstTargetFile:
        isFirstRow = firstRowIsHeading
        _writeRstSeparatorLine(rstTargetFile, lengths, "-")
        for row in rows:
            _writeRstRow(rstTargetFile, lengths, row)
            if isFirstRow:
                lineSeparator = "="
                isFirstRow = False
            else:
                lineSeparator = "-"
            _writeRstSeparatorLine(rstTargetFile, lengths, lineSeparator)


# FIXME: The handlers for the various formats should support items spawning multiple columns.
# FIXME: Add support for items spawning multiple rows.
def main(arguments):
    assert arguments is not None

    _FORMAT_CSV = "csv"
    _FORMAT_RST = "rst"
    _FORMATS = [_FORMAT_CSV, _FORMAT_RST]
    _DEFAULT_FORMAT = _FORMAT_CSV
    _DEFAULT_SHEET = 1

    parser = argparse.ArgumentParser(description='convert ODS file to other formats')
    parser.add_argument("-f", "--format", metavar="FORMAT", default=_DEFAULT_FORMAT, choices=sorted(_FORMATS),
            dest="format",
            help="target format: %s (default: %s)" % (_tools.humanReadableList(_FORMATS), _DEFAULT_FORMAT))
    parser.add_argument("-1", "--heading", action="store_true", dest="firstRowIsHeading",
            help="render first row as heading")
    parser.add_argument("-s", "--sheet", metavar="SHEET", default=_DEFAULT_SHEET, type=int, dest="sheet",
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
        args.target_path = _tools.withSuffix(args.source_ods_path, suffix)

    _log.info("convert %r to %r using format %r" % (args.source_ods_path, args.target_path, args.format))
    try:
        if args.format == _FORMAT_CSV:
            toCsv(args.source_ods_path, args.target_path, sheet=args.sheet)
        elif args.format == _FORMAT_RST:
            toRst(args.source_ods_path, args.target_path, firstRowIsHeading=args.firstRowIsHeading, sheet=args.sheet)
        else:  # pragma: no cover
            raise NotImplementedError("format=%r" % args.format)
    except EnvironmentError as error:
        _log.error("cannot convert ods: %s" % error)
        sys.exit(1)
    except Exception as error:
        _log.exception("cannot convert ods: %s" % error)
        sys.exit(1)

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
