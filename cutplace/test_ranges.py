"""
Tests for ranges.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
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

import ranges


class RangeTest(unittest.TestCase):
    """
    Test cases for ranges.
    """
    def testProperRanges(self):
        self.assertEquals(ranges.Range("1").items, [(1, 1)])
        self.assertEquals(ranges.Range("1:").items, [(1, None)])
        self.assertEquals(ranges.Range(":1").items, [(None, 1)])
        self.assertEquals(ranges.Range("1:2").items, [(1, 2)])
        self.assertEquals(ranges.Range("-1:2").items, [(-1, 2)])

    def testEmptyRange(self):
        self.assertEquals(ranges.Range("").items, None)
        self.assertEquals(ranges.Range(" ").items, None)

        # Another way to express an empty ranges.
        emptyRange = ranges.Range(None)
        self.assertEquals(emptyRange.items, None)

        # Range validation still works even with empty ranges.
        self.assertFalse(emptyRange.validate("name", 1))
        self.assertFalse(emptyRange.validate("name", -1))

    def testProperHexRanges(self):
        self.assertEquals(ranges.Range("0x7f").items, [(127, 127)])
        self.assertEquals(ranges.Range("0x7F").items, [(127, 127)])

    def testProperMultiRanges(self):
        self.assertEquals(ranges.Range("1, 3").items, [(1, 1), (3, 3)])
        self.assertEquals(ranges.Range("1:2, 5:").items, [(1, 2), (5, None)])

    def testSymbolicRange(self):
        self.assertEquals(ranges.Range("TAB").items, [(9, 9)])
        self.assertEquals(ranges.Range("vt").items, [(11, 11)])
        self.assertEquals(ranges.Range("Tab:Vt").items, [(9, 11)])
        self.assertEquals(ranges.Range("Tab:11").items, [(9, 11)])

    def testTextRange(self):
        self.assertEquals(ranges.Range("\"a\"").items, [(97, 97)])

    def testRangesWithDefault(self):
        self.assertEquals(ranges.Range("1:2", "2:3").items, [(1, 2)])
        self.assertEquals(ranges.Range("", "2:3").items, [(2, 3)])
        self.assertEquals(ranges.Range(" ", "2:3").items, [(2, 3)])

    def testBrokenOverlappingMultiRange(self):
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1:5, 2:3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1:, 2:3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, ":5, 2:3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, ":5, :3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, ":5, 1:")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, ":5, 2")

    def testBrokenRanges(self):
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "x")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, ":")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "-")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "-:")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1 x")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "-x")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1 2")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1:2 3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1:2-3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "1:2:3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "2:1")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "2:-3")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "-1:-3")
        try:
            ranges.Range("?")
            self.fail("test must fail with RangeSyntaxError")
        except ranges.RangeSyntaxError, error:
            self.assertEqual(str(error), "range must be specified using integer numbers, text, symbols and colon (:) but found: '?' [token type: 52]")
        try:
            ranges.Range("1.23")
            self.fail("test must fail with RangeSyntaxError")
        except ranges.RangeSyntaxError, error:
            self.assertEqual(str(error), "number must be an integer but is: '1.23'")

    def testBrokenSymbolicNames(self):
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "spam")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "Esc:Tab")

    def testBrokenTextRange(self):
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "\"ab\"")
        self.assertRaises(ranges.RangeSyntaxError, ranges.Range, "\"\"")

    def _testNoRange(self, text):
        noRange = ranges.Range(text)
        self.assertEqual(noRange.items, None)
        noRange.validate("x", 0)
        noRange.validate("x", 2 ** 32)
        noRange.validate("x", - (2 ** 32) - 1)

    def testNoRange(self):
        self._testNoRange(None)
        self._testNoRange("")
        self._testNoRange("  ")

    def testValidate(self):
        lowerAndUpperRange = ranges.Range("-1:1")
        lowerAndUpperRange.validate("x", - 1)
        lowerAndUpperRange.validate("x", 0)
        lowerAndUpperRange.validate("x", 1)
        self.assertRaises(ranges.RangeValueError, lowerAndUpperRange.validate, "x", - 2)
        self.assertRaises(ranges.RangeValueError, lowerAndUpperRange.validate, "x", 2)

        lowerRange = ranges.Range("1:")
        lowerRange.validate("x", 1)
        lowerRange.validate("x", 2)
        lowerRange.validate("x", 2 ** 32)
        self.assertRaises(ranges.RangeValueError, lowerRange.validate, "x", 0)

        upperRange = ranges.Range(":1")
        upperRange.validate("x", 1)
        upperRange.validate("x", - 2)
        upperRange.validate("x", - (2 ** 32) - 1)
        self.assertRaises(ranges.RangeValueError, upperRange.validate, "x", 2)

        multiRange = ranges.Range("1:4, 7:9")
        multiRange.validate("x", 1)
        multiRange.validate("x", 7)
        multiRange.validate("x", 9)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", - 3)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", 0)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", 5)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", 6)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", 10)
        self.assertRaises(ranges.RangeValueError, multiRange.validate, "x", 723)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
