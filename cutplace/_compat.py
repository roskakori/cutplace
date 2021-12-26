"""
Utility functions for compatibility with Python 2 and 3.

Part of the code found here is derived from
https://pypi.python.org/pypi/future and
https://docs.python.org/2/library/csv.html#examples.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
# TODO: Remove this entire module.
import csv
import io


def text_repr(text):
    return repr(text)


def token_io_readline(text):
    """
    A readline function that can be used by `tokenize.generate_tokens()`.
    Using `io.StringIO.readline` under Python 2 would result in
    ``TypeError: initial_value must be unicode or None, not str``.
    """
    assert text is not None
    return io.StringIO(text).readline


def csv_reader(source_text_stream, dialect=csv.excel, **keywords):
    return csv.reader(source_text_stream, dialect=dialect, **keywords)


def csv_writer(target_text_stream, dialect=csv.excel, **keywords):
    return csv.writer(target_text_stream, dialect=dialect, **keywords)
