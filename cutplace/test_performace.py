"""
Test cutplace performance.
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
import logging
import unittest

import dev_test
import _cutplace

class PerformanceTest(unittest.TestCase):
    """
    Test case for performance profiling.
    """

    def testCanProcessManyCustomers(self):
        icdOdsPath = dev_test.getTestIcdPath("customers.ods")
        locCsvPath = dev_test.getTestFile("input", "lots_of_customers.csv")
        dev_test.createLotsOfCustomersCsv(locCsvPath, customerCount=20000)
        exitCode = _cutplace.main(["test_performance.py", icdOdsPath, locCsvPath])
        self.assertEqual(exitCode, 0)


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    unittest.main()
