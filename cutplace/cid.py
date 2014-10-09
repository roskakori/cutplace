"""
Reading ICD-Files
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

from . import data
from xlrd import *


class Cid(object):
    def __init__(self):
        self._data_format = None

    def read(self, source_path):
        # TODO: Detect format and use proper reader.
        empty_allowed = True
        for row in excel_rows(source_path):
            if row != [] and row[0].lower() == 'd':
                empty_allowed = False
                _, name, value = row[:3]
                if self.data_format is None:
                    self.data_format = data.Dataformat(value)
                else:
                    self.data_format.set_property(name, value)
            elif row == [] and not empty_allowed:  # exits loop after data_format
                break
            elif row != [] and row[0].lower() != 'd':
                # raise error when value is not supported
                raise ValueError("Cell with the value %s is nor supported!" % row[0])


def excel_rows(self, source_path):
    book = open_workbook(source_path)
    sheet = book.sheet_by_index(0)
    for row_number in range(sheet.nrows()):
        yield sheet.row_values(row_number)