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

from cutplace import data
from cutplace import errors


class Cid():
    def __init__(self):
        self._data_format = None
        self._location = None

    def read(self, source_path, rows):
        # TODO: Detect format and use proper reader.
        self._location = errors.InputLocation(source_path, hasCell=True)
        for row in rows:
            if row:
                row_type = row[0].lower()
                row_data = (row[1:] + [''] * 7)[:7]
                if row_type == 'd':
                    name, value = row_data[:2]
                    self._location.advanceColumn()
                    if name == '':
                        raise errors.DataFormatSyntaxError('name of data format property must be specified', self._location)
                    self._location.advanceColumn()
                    if self._data_format is None:
                        self._data_format = data.Dataformat(value.lower(), self._location)
                    else:
                        self._data_format.set_property(name.lower(), value.lower())
                elif row_type == 'f':
                    #TODO: implement support for fieldformat
                    pass
                elif row_type == 'c':
                    #TODO: implement support for checks
                    pass
                elif row_type != '':
                    # Raise error when value is not supported.
                    raise errors.DataFormatSyntaxError('CID row type is "%s" but must be empty or one of: C, D, or F' \
                        % row_type, self._location)
            self._location.advanceLine()
