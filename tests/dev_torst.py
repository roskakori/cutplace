"""
Convert data file described by CID to ReStructured Text.
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
import io
import logging
import os
import sys

import cutplace
from cutplace import data
from cutplace import rowio

_log = logging.getLogger('torst')


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
            item = ''
        item_length = len(item)
        assert column_length >= item_length
        # FIXME: Add support for items containing line separators.
        if ('\n' in item) or ('\r' in item):
            raise NotImplementedError('item must not contain line separator: %r' % item)
        rst_target_file.write('+%s%s' % (item, ' ' * (column_length - item_length)))
    rst_target_file.write('+\n')


def _write_rst_separator_line(rst_target_file, column_lengths, line_separator):
    assert rst_target_file is not None
    assert column_lengths
    assert line_separator in ["-", "="]

    for column_length in column_lengths:
        rst_target_file.write("+")
        if column_length > 0:
            rst_target_file.write(line_separator * column_length)
    rst_target_file.write("+\n")


def _convert_to_rst(cid_path, data_path, target_rst_path, target_encoding='utf-8'):
    assert cid_path is not None
    assert data_path is not None

    _log.info('read CID from "%s"', cid_path)
    cid = cutplace.Cid(cid_path)
    data_format = cid.data_format
    if data_format.format != data.FORMAT_DELIMITED:
        raise NotImplementedError('format=%s' % data_format.format)
    if cid.data_format.header >= 2:
        raise NotImplementedError('cid.data_format.header=%s' % cid.data_format.header)
    first_row_is_heading = cid.data_format.header == 1

    _log.info('read data from "%s"', data_path)
    rows = list(rowio.delimited_rows(data_path, data_format))

    # Find out the length of each column.
    lengths = []
    for row_number, row in enumerate(rows):
        for column_index, item in enumerate(row):
            item_length = len(item)
            is_first_row = row_number == 0
            is_past_last_column = column_index == len(lengths)
            if is_first_row or is_past_last_column:
                lengths.append(item_length)
            elif lengths[column_index] < item_length:
                lengths[column_index] = item_length
    if len(lengths) == 0:
        raise ValueError('file must contain columns: "%s"' % data_path)
    for column_index in range(len(lengths)):
        if lengths[column_index] == 0:
            raise ValueError('column %d in file "%s" must not always be empty' % (column_index + 1, data_path))

    _log.info('write RST to "%s"', target_rst_path)
    with io.open(target_rst_path, mode='w', encoding=target_encoding) as rst_target_file:
        is_first_row = first_row_is_heading
        _write_rst_separator_line(rst_target_file, lengths, "-")
        for row_number, row in enumerate(rows):
            _write_rst_row(rst_target_file, lengths, row)
            is_first_row = row_number == 0
            if is_first_row and first_row_is_heading:
                line_separator = "="
            else:
                line_separator = "-"
            _write_rst_separator_line(rst_target_file, lengths, line_separator)


def main(arguments):
    assert arguments is not None

    parser = argparse.ArgumentParser(description='Convert data file described by CID to ReStructured Text')
    parser.add_argument('cid_path', metavar='CID-FILE', help='CID describing the data')
    parser.add_argument('data_path', metavar='DATA-FILE', help='source data file to convert to RST')
    parser.add_argument(
        'rst_path', metavar='RST-FILE', nargs='?',
        help='target RST file; default: same as DATA_FILE but with suffix *.rst')
    args = parser.parse_args(arguments)
    if args.rst_path is None:
        args.rst_path = os.path.splitext(args.data_path)[0] + '.rst'

    exit_code = 1
    try:
        _convert_to_rst(args.cid_path, args.data_path, args.rst_path)
        exit_code = 0
    except (EnvironmentError, OSError) as error:
        _log.error("cannot convert ods: %s", error)
    except Exception as error:
        _log.exception("cannot convert ods: %s", error)
    return exit_code


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
