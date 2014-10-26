"""
Test for `errors` module.
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
import unittest
import io

from cutplace import errors


class ErrorsTest(unittest.TestCase):
    """TestCase for errors module."""
    def test_can_work_with_input_location(self):
        location = errors.InputLocation("eggs.txt", hasColumn=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (1;1)")
        location.advanceColumn(3)
        self.assertEqual(location.column, 3)
        location.advanceColumn()
        self.assertEqual(location.column, 4)
        location.advanceLine()
        self.assertEqual(location.line, 1)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (2;1)")

        # Test input with cells.
        location = errors.InputLocation("eggs.csv", hasCell=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.cell, 0)
        self.assertEqual(str(location), "eggs.csv (R1C1)")
        location.advanceLine()
        location.advanceCell(17)
        self.assertEqual(str(location), "eggs.csv (R2C18)")

        # Test input with sheet.
        location = errors.InputLocation("eggs.ods", hasCell=True, hasSheet=True)
        self.assertEqual(str(location), "eggs.ods (Sheet1!R1C1)")
        location.advanceSheet()
        location.advanceLine()
        location.advanceCell(17)
        self.assertEqual(str(location), "eggs.ods (Sheet2!R2C18)")

        # Test StringIO input.
        input_stream = io.StringIO("hugo was here")
        location = errors.InputLocation(input_stream)
        self.assertEqual(str(location), "<io> (1)")


if __name__ == '__main__':
    unittest.main()
