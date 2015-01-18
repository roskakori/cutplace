"""
Tests for ranges.
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

from cutplace import errors
from cutplace import ranges
from tests import dev_test


class RangeTest(unittest.TestCase):

    """
    Test cases for ranges.
    """

    def test_proper_ranges(self):
        self.assertEquals(ranges.Range("1").items, [(1, 1)])
        self.assertEquals(ranges.Range("1...").items, [(1, None)])
        self.assertEquals(ranges.Range("...1").items, [(None, 1)])
        self.assertEquals(ranges.Range("1" + "\u2026" + "2").items, [(1, 2)])
        self.assertEquals(ranges.Range("-1...2").items, [(-1, 2)])

        self.assertEquals(ranges.Range("1:").items, [(1, None)])
        self.assertEquals(ranges.Range(":1").items, [(None, 1)])
        self.assertEquals(ranges.Range("1:2").items, [(1, 2)])
        self.assertEquals(ranges.Range("-1:2").items, [(-1, 2)])

    def test_empty_range(self):
        self.assertEquals(ranges.Range("").items, None)
        self.assertEquals(ranges.Range(" ").items, None)

        # Another way to express an empty ranges.
        empty_range = ranges.Range(None)
        self.assertEquals(empty_range.items, None)

        # Range validation still works even with empty ranges.
        self.assertFalse(empty_range.validate("name", 1))
        self.assertFalse(empty_range.validate("name", -1))

    def test_proper_hex_ranges(self):
        self.assertEquals(ranges.Range("0x7f").items, [(127, 127)])
        self.assertEquals(ranges.Range("0x7F").items, [(127, 127)])

    def test_proper_multi_ranges(self):
        self.assertEquals(ranges.Range("1, 3").items, [(1, 1), (3, 3)])
        self.assertEquals(ranges.Range("1...2, 5...").items, [(1, 2), (5, None)])

    def test_symbolic_range(self):
        self.assertEquals(ranges.Range("TAB").items, [(9, 9)])
        self.assertEquals(ranges.Range("vt").items, [(11, 11)])
        self.assertEquals(ranges.Range("Tab...Vt").items, [(9, 11)])
        self.assertEquals(ranges.Range("Tab...11").items, [(9, 11)])

    def test_text_range(self):
        self.assertEquals(ranges.Range("\"a\"").items, [(97, 97)])

    def test_ranges_with_default(self):
        self.assertEquals(ranges.Range("1...2", "2...3").items, [(1, 2)])
        # self.assertEquals(ranges.Range("", "2...3").items, [None, (2, 3)])
        # self.assertEquals(ranges.Range("", "2...3").items, [(2, 3)])

    def test_can_get_lower_limit(self):
        self.assertEquals(ranges.Range("5...9").lower_limit, 5)
        self.assertEquals(ranges.Range("0...").lower_limit, 0)
        self.assertEquals(ranges.Range("...0").lower_limit, None)
        self.assertEquals(ranges.Range("...1, 3...").lower_limit, None)
        self.assertEquals(ranges.Range("5...9").lower_limit, 5)
        self.assertEquals(ranges.Range("1...2, 5...9").lower_limit, 1)

    def test_can_get_upper_limit(self):
        self.assertEquals(ranges.Range("1...2").upper_limit, 2)
        self.assertEquals(ranges.Range("0...").upper_limit, None)
        self.assertEquals(ranges.Range("...0").upper_limit, 0)
        self.assertEquals(ranges.Range("...1, 3...").upper_limit, None)
        self.assertEquals(ranges.Range("1...2, 5...9").upper_limit, 9)

    def test_broken_overlapping_multi_range(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "1...5, 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "1..., 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 2...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, ...3")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 1...")
        self.assertRaises(errors.InterfaceError, ranges.Range, "...5, 2")

    def test_broken_ranges(self):
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
        try:
            ranges.Range("?")
            self.fail("test must fail with InterfaceError")
        except errors.InterfaceError as error:
            dev_test.assert_fnmatches(
                self, str(error),
                "range must be specified using integer numbers, text, symbols and ellipsis (...) but found: '?'*")

        # Test is obsoleted because the range now supports float to
        # try:
        #     ranges.Range("1.23")
        #     self.fail("test must fail with InterfaceError")
        # except errors.InterfaceError as error:
        #     self.assertEqual(str(error), "number must be an integer but is: '1.23'")

    def test_broken_symbolic_names(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "spam")
        self.assertRaises(errors.InterfaceError, ranges.Range, "Esc...Tab")

    def test_broken_text_range(self):
        self.assertRaises(errors.InterfaceError, ranges.Range, "\"ab\"")
        self.assertRaises(errors.InterfaceError, ranges.Range, "\"\"")

    def _test_no_range(self, text):
        no_range = ranges.Range(text)
        self.assertEqual(no_range.items, None)
        no_range.validate("x", 0)
        no_range.validate("x", 2 ** 32)
        no_range.validate("x", - (2 ** 32) - 1)

    def test_no_range(self):
        self._test_no_range(None)
        self._test_no_range("")
        self._test_no_range("  ")

    def test_validate(self):
        lower_and_upper_range = ranges.Range("-1...1")
        lower_and_upper_range.validate("x", - 1)
        lower_and_upper_range.validate("x", 0)
        lower_and_upper_range.validate("x", 1)
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", - 2)
        self.assertRaises(errors.RangeValueError, lower_and_upper_range.validate, "x", 2)

        lower_range = ranges.Range("1...")
        lower_range.validate("x", 1)
        lower_range.validate("x", 2)
        lower_range.validate("x", 2 ** 32)
        self.assertRaises(errors.RangeValueError, lower_range.validate, "x", 0)

        upper_range = ranges.Range("...1")
        upper_range.validate("x", 1)
        upper_range.validate("x", - 2)
        upper_range.validate("x", - (2 ** 32) - 1)
        self.assertRaises(errors.RangeValueError, upper_range.validate, "x", 2)

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
