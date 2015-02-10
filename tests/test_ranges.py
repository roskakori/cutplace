"""
Tests for :py:mod:`ranges`.
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

import unittest
import decimal

from cutplace import errors
from cutplace import ranges
from tests import dev_test


class RangeTest(unittest.TestCase):

    """
    Test cases for :py:class:`cutplace.ranges.Range`.
    """
    def test_can_parse_proper_ranges(self):
        self.assertEqual(ranges.Range("1").items, [(1, 1)])
        self.assertEqual(ranges.Range("1...").items, [(1, None)])
        self.assertEqual(ranges.Range("...1").items, [(None, 1)])
        self.assertEqual(ranges.Range("1" + "\u2026" + "2").items, [(1, 2)])
        self.assertEqual(ranges.Range("-1...2").items, [(-1, 2)])

        self.assertEqual(ranges.Range("1:").items, [(1, None)])
        self.assertEqual(ranges.Range(":1").items, [(None, 1)])
        self.assertEqual(ranges.Range("1:2").items, [(1, 2)])
        self.assertEqual(ranges.Range("-1:2").items, [(-1, 2)])

    def _test_can_handle_empty_range(self, description):
        empty_range = ranges.Range(description)
        self.assertEqual(empty_range.items, None)
        self.assertEqual(empty_range.lower_limit, None)
        self.assertEqual(empty_range.upper_limit, None)
        self.assertIsNone(empty_range.validate("x", ranges.MIN_INTEGER - 1))
        self.assertIsNone(empty_range.validate("x", 1))
        self.assertIsNone(empty_range.validate("x", 0))
        self.assertIsNone(empty_range.validate("x", -1))
        self.assertIsNone(empty_range.validate("x", ranges.MAX_INTEGER + 1))

    def test_can_handle_empty_range(self):
        self._test_can_handle_empty_range(None)
        self._test_can_handle_empty_range('')
        self._test_can_handle_empty_range(' \t  ')

    def test_can_parse_hex_range(self):
        self.assertEqual(ranges.Range("0x7f").items, [(127, 127)])
        self.assertEqual(ranges.Range("0x7F").items, [(127, 127)])

    def test_can_parse_multiple_ranges(self):
        self.assertEqual(ranges.Range("1, 3").items, [(1, 1), (3, 3)])
        self.assertEqual(ranges.Range("1...2, 5...").items, [(1, 2), (5, None)])

    def test_can_parse_symbolic_range(self):
        self.assertEqual(ranges.Range("TAB").items, [(9, 9)])
        self.assertEqual(ranges.Range("vt").items, [(11, 11)])
        self.assertEqual(ranges.Range("Tab...Vt").items, [(9, 11)])
        self.assertEqual(ranges.Range("Tab...11").items, [(9, 11)])

    def test_can_parse_text_range(self):
        self.assertEqual(ranges.Range("\"a\"").items, [(97, 97)])

    def test_can_use_default_range(self):
        self.assertEqual(ranges.Range("", "2...3").items, [(2, 3)])

    def test_can_override_default_range(self):
        self.assertEqual(ranges.Range("1...2", "2...3").items, [(1, 2)])

    def test_can_get_lower_limit(self):
        self.assertEqual(ranges.Range("5...9").lower_limit, 5)
        self.assertEqual(ranges.Range("0...").lower_limit, 0)
        self.assertEqual(ranges.Range("...0").lower_limit, None)
        self.assertEqual(ranges.Range("...1, 3...").lower_limit, None)
        self.assertEqual(ranges.Range("5...9").lower_limit, 5)
        self.assertEqual(ranges.Range("1...2, 5...9").lower_limit, 1)
        self.assertEqual(ranges.Range("5...9, 1...2").lower_limit, 1)

    def test_can_get_upper_limit(self):
        self.assertEqual(ranges.Range("1...2").upper_limit, 2)
        self.assertEqual(ranges.Range("0...").upper_limit, None)
        self.assertEqual(ranges.Range("...0").upper_limit, 0)
        self.assertEqual(ranges.Range("...1, 3...").upper_limit, None)
        self.assertEqual(ranges.Range("1...2, 5...9").upper_limit, 9)

    def test_fails_on_inconsistent_overlapping_multi_range(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "1...5, 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1..., 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, ...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 1...")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 2")

    def _test_fails_with_interface_error(self, description, anticipated_error_message_pattern):
        try:
            ranges.Range(description)
            self.fail("test must fail with InterfaceError")
        except errors.InterfaceError as anticipated_error:
            dev_test.assert_fnmatches(self, str(anticipated_error), anticipated_error_message_pattern)

    def test_fails_on_broken_ranges(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "x")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...")
        self.assertRaises(errors.InterfaceError, ranges.Range, "-")
        self.assertRaises(errors.InterfaceError, ranges.Range, "-...")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1 x")
        self.assertRaises(errors.InterfaceError, ranges.Range, "-x")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1 2")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1...2 3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1...2-3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1...2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "2...1")
        self.assertRaises(errors.InterfaceError, ranges.Range, "2...-3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "-1...-3")
        self._test_fails_with_interface_error(
            '?', "range must be specified using integer numbers, text, symbols and ellipsis (...) but found: '?'*")

    def test_fails_on_floating_point_number(self):
        self._test_fails_with_interface_error(
            '1.23', "numeric value for range must be an integer number but is: '1.23'")

    def test_fails_on_unknown_symbolic_name(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "spam")

    def test_fails_on_inconsistent_symbolic_names(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "Cr...Tab")

    def test_fails_on_string_with_multiple_characters(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "\"ab\"")

    def test_fails_on_unterminated_string(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "\"\"")

    def test_can_validate_with_lower_and_upper_limit(self):
        lower_and_upper_range = ranges.Range("-1...1")
        lower_and_upper_range.validate("x", - 1)
        lower_and_upper_range.validate("x", 0)
        lower_and_upper_range.validate("x", 1)
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", - 2)
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", 2)

    def test_can_validate_with_lower_limit_only(self):
        lower_range = ranges.Range("1...")
        lower_range.validate("x", 1)
        lower_range.validate("x", 2)
        lower_range.validate("x", 2 ** 32)
        self.assertRaises(errors.RangeValueError, lower_range.validate, "x", 0)

    def test_can_validate_with_upper_limit_only(self):
        upper_range = ranges.Range("...1")
        upper_range.validate("x", 1)
        upper_range.validate("x", - 2)
        upper_range.validate("x", - (2 ** 32) - 1)
        self.assertRaises(errors.RangeValueError, upper_range.validate, "x", 2)

    def test_can_validate_with_multi_range(self):
        multi_range = ranges.Range("1...4, 7...9")
        multi_range.validate("x", 1)
        multi_range.validate("x", 7)
        multi_range.validate("x", 9)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", - 3)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 0)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 5)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 6)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 10)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 723)

    def test_can_create_range_from_length(self):
        self.assertEqual(ranges.create_range_from_length(ranges.Range("1...")).items, None)
        self.assertEqual(ranges.create_range_from_length(ranges.Range("1...1")).items, [(0, 9)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("1...3")).items, [(-99, 999)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("0...")).items, None)
        self.assertEqual(ranges.create_range_from_length(ranges.Range("0...1")).items, [(0, 9)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("0...3")).items, [(-99, 999)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("")).items, None)
        self.assertEqual(ranges.create_range_from_length(ranges.Range("...1")).items, [(0, 9)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("...3")).items, [(-99, 999)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("2...2")).items, [(-9, -1), (10, 99)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("2...5")).items, [(-9999, -1), (10, 99999)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("3...8")).items, [(-9999999, -10), (100, 99999999)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("2...")).items, [(None, -1), (10, None)])
        self.assertEqual(ranges.create_range_from_length(ranges.Range("3...")).items, [(None, -10), (100, None)])
        self.assertEqual(
            ranges.create_range_from_length(
                ranges.Range("3...4, 10...")).items, [(-999, -10), (100, 9999), (None, -100000000), (1000000000, None)])

    def test_fails_on_create_range_from_negative_length(self):
        self.assertRaises(errors.RangeValueError, ranges.create_range_from_length, ranges.Range("-19...-1"))
        self.assertRaises(errors.RangeValueError, ranges.create_range_from_length, ranges.Range("-19...1"))
        self.assertRaises(errors.RangeValueError, ranges.create_range_from_length, ranges.Range("-1...0"))
        self.assertRaises(errors.RangeValueError, ranges.create_range_from_length, ranges.Range("0...0"))


class DecimalRangeTest(unittest.TestCase):

    def test_can_handle_proper_decimal_ranges(self):
        self.assertEquals(ranges.DecimalRange("1.1").items, [(decimal.Decimal('1.1'), decimal.Decimal('1.1'))])
        self.assertEquals(ranges.DecimalRange("1...").items, [(1, None)])
        self.assertEquals(ranges.DecimalRange("...1.").items, [(None, decimal.Decimal('1'))])
        self.assertEquals(ranges.DecimalRange("1.1" + "\u2026" + "2.1").items, [(decimal.Decimal('1.1'), decimal.Decimal('2.1'))])
        self.assertEquals(ranges.DecimalRange("-1.1...2").items, [(decimal.Decimal('-1.1'), 2)])

        self.assertEquals(ranges.DecimalRange("1.1:").items, [(decimal.Decimal('1.1'), None)])
        self.assertEquals(ranges.DecimalRange(":1.1").items, [(None, decimal.Decimal('1.1'))])
        self.assertEquals(ranges.DecimalRange("1.1:2.1").items, [(decimal.Decimal('1.1'), decimal.Decimal('2.1'))])
        self.assertEquals(ranges.DecimalRange("-1.1:2.1").items, [(decimal.Decimal('-1.1'), decimal.Decimal('2.1'))])

    def test_can_validate_values(self):
        lower_and_upper_range = ranges.DecimalRange("-1.2...1.5")
        lower_and_upper_range.validate("x", '-1.1')
        lower_and_upper_range.validate("x", 0)
        lower_and_upper_range.validate("x", 1)

        lower_range = ranges.DecimalRange("1.1...")
        lower_range.validate("x", '1.1')
        lower_range.validate("x", 2)
        lower_range.validate("x", 2 ** 32)

        upper_range = ranges.DecimalRange("...1.1")
        upper_range.validate("x", '1.1')
        upper_range.validate("x", - 2)
        upper_range.validate("x", - (2 ** 32) - 1)

        multi_range = ranges.DecimalRange("1.1...4.9, 7.1...9")
        multi_range.validate("x", '1.1')
        multi_range.validate("x", '4.9')
        multi_range.validate("x", '7.1')
        multi_range.validate("x", 9)

    def test_fails_on_validation_with_out_of_range_value(self):
        lower_and_upper_range = ranges.DecimalRange("-1.2...1.5")
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", decimal.Decimal('-1.3'))
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", decimal.Decimal('1.6'))

        lower_range = ranges.DecimalRange("1.1...")
        self.assertRaises(errors.RangeValueError, lower_range.validate, "x", 1)

        upper_range = ranges.DecimalRange("...1.1")
        self.assertRaises(errors.RangeValueError, upper_range.validate, "x", decimal.Decimal('1.2'))

        multi_range = ranges.DecimalRange("1.1...4.9, 7.1...9")
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 1)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 5)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", 7)
        self.assertRaises(errors.RangeValueError, multi_range.validate, "x", decimal.Decimal('9.1'))

    def _test_can_handle_empty_range(self, description):
        empty_range = ranges.DecimalRange(description)
        self.assertEquals(empty_range.items, None)
        self.assertEquals(empty_range.lower_limit, None)
        self.assertEquals(empty_range.upper_limit, None)
        self.assertIsNone(empty_range.validate("x", decimal.Decimal(ranges.MIN_DECIMAL_TEXT) - 1))
        self.assertIsNone(empty_range.validate("x", decimal.Decimal('1.1')))
        self.assertIsNone(empty_range.validate("x", 0))
        self.assertIsNone(empty_range.validate("x", decimal.Decimal('-1.1')))
        self.assertIsNone(empty_range.validate("x", decimal.Decimal(ranges.MAX_DECIMAL_TEXT) + 1))

    def test_can_handle_empty_range(self):
        self._test_can_handle_empty_range(None)
        self._test_can_handle_empty_range('')
        self._test_can_handle_empty_range(' \t  ')

    def _test_fails_with_interface_error(self, description, anticipated_error_message_pattern):
        try:
            ranges.DecimalRange(description)
            self.fail("test must fail with InterfaceError")
        except errors.InterfaceError as anticipated_error:
            dev_test.assert_fnmatches(self, str(anticipated_error), anticipated_error_message_pattern)

    def test_broken_ranges(self):
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "x")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "...")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "-")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "-...")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1.1 x")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "-x")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1.1 2.3")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1.2...2.3 3.4")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1.1...2-3")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1.1...2.3...3.4")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "2.3...1.3")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "2.2...-3.3")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "-1.2...-3.4")
        self._test_fails_with_interface_error(
            '?', "range must be specified using integer numbers and ellipsis (...) but found: '?'*")

    def test_fails_on_parse_hex_range(self):
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "0x7f")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "0x7F")

    def test_can_parse_multiple_ranges(self):
        self.assertEquals(ranges.DecimalRange("1.1, 3").items, [(decimal.Decimal('1.1'), decimal.Decimal('1.1')), (3, 3)])
        self.assertEquals(ranges.DecimalRange("1...2.3, 5...").items, [(1, decimal.Decimal('2.3')), (5, None)])

    def test_fails_on_parse_symbolic_range(self):
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "TAB")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "vt")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "Tab...Vt")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "Tab...11")

    def test_fails_on_parse_text_range(self):
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "\"a\"")

    def test_can_use_default_range(self):
        self.assertEquals(ranges.DecimalRange("", "2.1...3").items, [(decimal.Decimal('2.1'), 3)])

    def test_can_override_default_range(self):
        self.assertEquals(ranges.DecimalRange("1.1...2", "2...3").items, [(decimal.Decimal('1.1'), 2)])

    def test_can_get_lower_limit(self):
        self.assertEquals(ranges.DecimalRange("5.5...9").lower_limit, decimal.Decimal('5.5'))
        self.assertEquals(ranges.DecimalRange("0...").lower_limit, 0)
        self.assertEquals(ranges.DecimalRange("...0").lower_limit, None)
        self.assertEquals(ranges.DecimalRange("...1, 3...").lower_limit, None)
        self.assertEquals(ranges.DecimalRange("5...9").lower_limit, 5)
        self.assertEquals(ranges.DecimalRange("1.1...2, 5...9").lower_limit, decimal.Decimal('1.1'))
        self.assertEquals(ranges.DecimalRange("5...9, 1.1...2").lower_limit, decimal.Decimal('1.1'))

    def test_can_get_upper_limit(self):
        self.assertEquals(ranges.DecimalRange("1...2.1").upper_limit, decimal.Decimal('2.1'))
        self.assertEquals(ranges.DecimalRange("0...").upper_limit, None)
        self.assertEquals(ranges.DecimalRange("...0").upper_limit, 0)
        self.assertEquals(ranges.DecimalRange("...1, 3...").upper_limit, None)
        self.assertEquals(ranges.DecimalRange("1...2, 5...9.3").upper_limit, decimal.Decimal('9.3'))

    def test_can_process_empty_range(self):
        self.assertEqual(ranges.DecimalRange("").items, None)

    def test_fails_on_inconsistent_overlapping_multi_range(self):
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1...2.4, 2.3...3.4")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "1..., 2...3.1")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "...5.9, 2...3")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "...5, ...4.9")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "...5, 1...")
        self.assertRaises(errors.InterfaceError, ranges.DecimalRange, "...5, 2")

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
