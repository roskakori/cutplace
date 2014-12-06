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
    """
    TestCase for `errors` module.
    """

    def test_can_work_with_location(self):
        location = errors.Location("eggs.txt", has_column=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (1;1)")
        location.advance_column(3)
        self.assertEqual(location.column, 3)
        location.advance_column()
        self.assertEqual(location.column, 4)
        location.advance_line()
        self.assertEqual(location.line, 1)
        self.assertEqual(location.column, 0)
        self.assertEqual(str(location), "eggs.txt (2;1)")

        # Test input with cells.
        location = errors.Location("eggs.csv", has_cell=True)
        self.assertEqual(location.line, 0)
        self.assertEqual(location.cell, 0)
        self.assertEqual(str(location), "eggs.csv (R1C1)")
        location.advance_line()
        location.advance_cell(17)
        self.assertEqual(location.__repr__(), "eggs.csv (R2C18)")

        # Test input with sheet.
        location = errors.Location("eggs.ods", has_cell=True, has_sheet=True)
        self.assertEqual(str(location), "eggs.ods (Sheet1!R1C1)")
        location.advance_sheet()
        location.advance_line()
        location.advance_cell(17)
        location._set_sheet(4)
        self.assertEqual(str(location), "eggs.ods (Sheet5!R2C18)")

        # Test StringIO input.
        input_stream = io.StringIO("hugo was here")
        location = errors.Location(input_stream)
        self.assertEqual(str(location), "<io> (1)")

    def test_can_compare_two_locations(self):
        location = errors.Location("eggs.ods", has_cell=True, has_sheet=True)
        location_other = errors.Location("eggs.ods", has_cell=True, has_sheet=True)
        self.assertEqual(location.__eq__(location_other), True)
        self.assertEqual(location.__lt__(location_other), False)

    def test_can_create_cutplace_error(self):
        location = errors.Location("eggs.ods", has_cell=True, has_sheet=True)
        base_error = errors.CutplaceError("It`s a test", location, "see also message", location, "cause")
        self.assertEqual(base_error.location, location)
        self.assertEqual(base_error.see_also_location, location)
        self.assertEqual(base_error.cause, "cause")
        self.assertEqual(base_error.__str__(), 'eggs.ods (Sheet1!R1C1): It`s a test (see also: eggs.ods (Sheet1!R1C1):'
                                               ' see also message)')

if __name__ == '__main__':
    unittest.main()
