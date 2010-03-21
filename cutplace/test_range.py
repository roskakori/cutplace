"""
Tests for ranges.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import range
import unittest

class RangeTest(unittest.TestCase):
    """
    Test cases for Range.
    """
    def testProperRanges(self):
        self.assertEquals(range.Range("").items, None)
        self.assertEquals(range.Range(" ").items, None)
        self.assertEquals(range.Range("1").items, [(1, 1)])
        self.assertEquals(range.Range("1:").items, [(1, None)])
        self.assertEquals(range.Range(":1").items, [(None, 1)])
        self.assertEquals(range.Range("1:2").items, [(1, 2)])
        self.assertEquals(range.Range("-1:2").items, [(-1, 2)])

    def testProperMultiRanges(self):
        self.assertEquals(range.Range("1, 3").items, [(1, 1), (3, 3)])
        self.assertEquals(range.Range("1:2, 5:").items, [(1, 2), (5, None)])

    def testRangesWithDefault(self):
        self.assertEquals(range.Range("1:2", "2:3").items, [(1, 2)])
        self.assertEquals(range.Range("", "2:3").items, [(2, 3)])
        self.assertEquals(range.Range(" ", "2:3").items, [(2, 3)])

    def testBrokenOverlappingMultiRange(self):
        self.assertRaises(range.RangeSyntaxError, range.Range, "1:5, 2:3")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1:, 2:3")
        self.assertRaises(range.RangeSyntaxError, range.Range, ":5, 2:3")
        self.assertRaises(range.RangeSyntaxError, range.Range, ":5, :3")
        self.assertRaises(range.RangeSyntaxError, range.Range, ":5, 1:")
        self.assertRaises(range.RangeSyntaxError, range.Range, ":5, 2")
        
    def testBrokenRanges(self):
        self.assertRaises(range.RangeSyntaxError, range.Range, "x")
        self.assertRaises(range.RangeSyntaxError, range.Range, ":")
        self.assertRaises(range.RangeSyntaxError, range.Range, "-")
        self.assertRaises(range.RangeSyntaxError, range.Range, "-:")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1 x")
        self.assertRaises(range.RangeSyntaxError, range.Range, "-x")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1 2")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1:2 3")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1:2-3")
        self.assertRaises(range.RangeSyntaxError, range.Range, "1:2:3")
        self.assertRaises(range.RangeSyntaxError, range.Range, "2:1")
        self.assertRaises(range.RangeSyntaxError, range.Range, "2:-3")
        self.assertRaises(range.RangeSyntaxError, range.Range, "-1:-3")
    
    def _testNoRange(self, text):
        noRange = range.Range(text)
        self.assertEqual(noRange.items, None)
        noRange.validate("x", 0)
        noRange.validate("x", 2 ** 32)
        noRange.validate("x", - (2 ** 32) - 1)

    def testNoRange(self):
        self._testNoRange(None)
        self._testNoRange("")
        self._testNoRange("  ")

    def testValidate(self):
        lowerAndUpperRange = range.Range("-1:1")
        lowerAndUpperRange.validate("x", - 1)
        lowerAndUpperRange.validate("x", 0)
        lowerAndUpperRange.validate("x", 1)
        self.assertRaises(range.RangeValueError, lowerAndUpperRange.validate, "x", - 2)
        self.assertRaises(range.RangeValueError, lowerAndUpperRange.validate, "x", 2)
        
        lowerRange = range.Range("1:") 
        lowerRange.validate("x", 1)
        lowerRange.validate("x", 2)
        lowerRange.validate("x", 2 ** 32)
        self.assertRaises(range.RangeValueError, lowerRange.validate, "x", 0)

        upperRange = range.Range(":1") 
        upperRange.validate("x", 1)
        upperRange.validate("x", - 2)
        upperRange.validate("x", - (2 ** 32) - 1)
        self.assertRaises(range.RangeValueError, upperRange.validate, "x", 2)
        
        multiRange = range.Range("1:4, 7:9") 
        multiRange.validate("x", 1)
        multiRange.validate("x", 7)
        multiRange.validate("x", 9)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", - 3)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", 0)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", 5)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", 6)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", 10)
        self.assertRaises(range.RangeValueError, multiRange.validate, "x", 723)
        

if __name__ == "__main__": # pragma: no cover
    unittest.main()