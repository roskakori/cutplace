"""
Tests for `checks` module.
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

import logging
import unittest

from cutplace import checks
from cutplace import errors

_TEST_FIELD_NAMES = 'branch_id customer_id first_name surname gender date_of_birth'.split()


def _create_field_map(field_names, field_values):
    assert field_names
    assert field_values
    assert len(field_names) == len(field_values)

    return dict(zip(field_names, field_values))


class _AbstractCheckTest(unittest.TestCase):
    def test_can_represent_check_as_str(self):
        field_names = _TEST_FIELD_NAMES
        # TODO: Create an instance of the current class instead of AbstractCheck even for ancestors.
        check = checks.AbstractCheck("test check", "", field_names)
        self.assertTrue(check.__str__())

    def test_has_location(self):
        field_names = _TEST_FIELD_NAMES
        check = checks.AbstractCheck("test check", "", field_names)
        self.assertTrue(check.location is not None)

    def test_has_field_names(self):
        field_names = _TEST_FIELD_NAMES
        check = checks.AbstractCheck("test check", "", field_names)
        self.assertEqual(field_names, check.field_names)

    def test_fails_on_missing_field_names(self):
        self.assertRaises(errors.InterfaceError, checks.AbstractCheck, "missing fields", "", [])

    def test_can_check_empty_row(self):
        # HACK: This is just here to make coverage happy because "# pragma: no cover" does not work
        # on methods that consist of nothing but a single "pass".
        field_names = _TEST_FIELD_NAMES
        check = checks.AbstractCheck("test check", "", field_names)
        location = errors.Location(self.test_can_check_empty_row, has_cell=True)
        check.check_row([], location)


class IsUniqueCheckTest(_AbstractCheckTest):
    def test_fails_on_duplicate_with_single_field(self):
        field_names = ['customer_id']
        check = checks.IsUniqueCheck('test check', 'customer_id', field_names)
        location = errors.Location(self.test_fails_on_duplicate_with_single_field, has_cell=True)
        check.check_row(_create_field_map(field_names, [1]), location)
        location.advance_line()
        check.check_row(_create_field_map(field_names, [2]), location)
        location.advance_line()
        try:
            check.check_row(_create_field_map(field_names, [1]), location)
            self.fail('duplicate row must cause CheckError')
        except errors.CheckError as error:
            self.assertTrue(error.see_also_location)
            self.assertNotEqual(location, error.see_also_location)
            self.assertEqual(error.location.cell, 0)

        # These methods should not do anything, but call them anyway for tests sake.
        check.check_at_end(location)
        check.cleanup()

    def test_fails_on_duplicate_with_multiple_fields(self):
        field_names = _TEST_FIELD_NAMES
        check = checks.IsUniqueCheck("test check", "branch_id, customer_id", field_names)
        location = errors.Location(self.test_fails_on_duplicate_with_multiple_fields, has_cell=True)
        check.check_row(_create_field_map(field_names, [38000, 23, "John", "Doe", "male", "08.03.1957"]), location)
        location.advance_line()
        check.check_row(_create_field_map(field_names, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        location.advance_line()
        try:
            check.check_row(_create_field_map(field_names, [38000, 59, "Jane", "Miller", "female", "04.10.1946"]),
                            location)
            self.fail("duplicate row must cause CheckError")
        except errors.CheckError as error:
            self.assertTrue(error.see_also_location)
            self.assertNotEqual(location, error.see_also_location)
            self.assertEqual(error.location.cell, 0)

        # These methods should not do anything, but call them anyway for tests sake.
        check.check_at_end(location)
        check.cleanup()

    def test_fails_on_rule_without_fields(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "", field_names)
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "   ", field_names)

    def test_fails_on_rule_with_two_consecutive_commas(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "branch_id,,customer_id",
                field_names)
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "branch_id,,", field_names)

    def test_fails_on_rule_starting_with_comma(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", ",branch_id", field_names)

    def test_fails_on_rule_with_broken_field_name(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "branch_id, customer-id",
                field_names)

    def test_fails_on_rule_with_missing_comma_between_field_names(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", "branch_id customer_id",
                field_names)

    def test_fails_on_rule_with_duplicate_field_name(self):
        field_names = _TEST_FIELD_NAMES
        first_field_name = field_names[0]
        broken_unique_field_names = ", ".join([first_field_name, first_field_name])
        self.assertRaises(errors.InterfaceError, checks.IsUniqueCheck, "test check", broken_unique_field_names,
                field_names)


class DistinctCountCheckTest(unittest.TestCase):
    def test_fails_on_too_many_distinct_values(self):
        field_names = _TEST_FIELD_NAMES
        checks.DistinctCountCheck("test check", "branch_id<3", field_names)
        check = checks.DistinctCountCheck("test check", "branch_id < 3", field_names)
        location = errors.Location(self.test_fails_on_too_many_distinct_values, has_cell=True)
        check.check_row(_create_field_map(field_names, [38000, 23, "John", "Doe", "male", "08.03.1957"]), location)
        location.advance_line()
        check.check_row(_create_field_map(field_names, [38001, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        check.check_at_end(location)
        location.advance_line()
        check.check_row(_create_field_map(field_names, [38003, 59, "Jane", "Miller", "female", "04.10.1946"]), location)
        self.assertRaises(errors.CheckError, check.check_at_end, location)

    def test_fails_on_broken_check_rule(self):
        field_names = _TEST_FIELD_NAMES
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken", "", field_names)
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken", " ", field_names)
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken", "hugo < 3", field_names)
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken", "branch_id < (100 / 0)",
                field_names)
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken",
                "branch_id ! broken ^ 5ynt4x ?!?", field_names)
        self.assertRaises(errors.InterfaceError, checks.DistinctCountCheck, "broken", "branch_id + 123", field_names)

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
