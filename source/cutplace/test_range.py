import range
import unittest

class RangeTest(unittest.TestCase):
    """
    Test cases for Range.
    """
    def testProperRanges(self):
        self.assertEquals(range.Range("").items, [])
        self.assertEquals(range.Range(" ").items, [])
        self.assertEquals(range.Range("1").items, [(1, 1)])
        self.assertEquals(range.Range("1:").items, [(1, None)])
        self.assertEquals(range.Range(":1").items, [(None, 1)])
        self.assertEquals(range.Range("1:2").items, [(1, 2)])
        self.assertEquals(range.Range("-1:2").items, [(-1, 2)])

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
        upperRange.validate("x", -2)
        upperRange.validate("x", - (2 ** 32) - 1)
        self.assertRaises(range.RangeValueError, upperRange.validate, "x", 2)

if __name__ == "__main__":
    unittest.main()