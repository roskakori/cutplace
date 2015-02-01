"""
Tests for :py:mod:`cutplace.errors` module.
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

import io
import unittest

from cutplace import errors
from tests import dev_test


class LocationTest(unittest.TestCase):
    def test_can_work_with_location(self):
        # TODO: Cleanup: split up in several tests with meaningful names.
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

    def test_can_create_caller_location(self):
        location = errors.create_caller_location()
        dev_test.assert_fnmatches(self, str(location), 'test_errors.py ([1-9]*)')


class CutplaceErrorTest(unittest.TestCase):
    def test_can_create_simple_cutplace_error(self):
        location = errors.Location('eggs.ods', has_cell=True, has_sheet=True)
        error = errors.CutplaceError('something must be something else', location)
        self.assertEqual(error.location, location)
        self.assertEqual(error.__str__(), 'eggs.ods (Sheet1!R1C1): something must be something else')

    def test_can_create_cutplace_error_with_see_also_details(self):
        location = errors.Location('eggs.ods', has_cell=True, has_sheet=True)
        location.advance_line(3)
        location.advance_cell(2)
        location_of_cause = errors.Location('spam.ods', has_cell=True, has_sheet=True)
        cause = errors.CutplaceError('something must be something else', location_of_cause)
        error = errors.CutplaceError('cannot do something', location, cause.message, cause.location, cause)
        self.assertEqual(error.location, location)
        self.assertEqual(error.see_also_location, cause.location)
        self.assertEqual(error.cause, cause)
        self.assertEqual(
            error.__str__(),
            'eggs.ods (Sheet1!R4C3): cannot do something '
            + '(see also: spam.ods (Sheet1!R1C1): something must be something else)')


if __name__ == '__main__':
    unittest.main()
