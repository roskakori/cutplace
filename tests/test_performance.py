"""
Test cutplace performance.
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
import io
import logging
import os.path
import unittest

from cutplace import dev_test
from cutplace import _cutplace
from cutplace import _tools

_log = logging.getLogger("cutplace.dev_reports")
_hasProfiler = False

try:
    import cProfile
    import pstats
    _hasProfiler = True
except ImportError as error:
    _log.warning("cannot test performance: %s", error)


def _buildAndValidateManyCustomers():
    icdOdsPath = dev_test.getTestIcdPath("customers.ods")
    locCsvPath = dev_test.getTestFile("input", "lots_of_customers.csv")
    dev_test.createLotsOfCustomersCsv(locCsvPath, customerCount=20000)
    exitCode = _cutplace.main(["test_performance.py", icdOdsPath, locCsvPath])
    if exitCode != 0:
        raise ValueError("exit code of performance test must be 0 but is %d" % exitCode)


class PerformanceTest(unittest.TestCase):
    """
    Test case for performance profiling.
    """
    def testCanValidateManyCustomers(self):
        if _hasProfiler:
            targetBasePath = os.path.join("build", "site", "reports")
            itemName = "profile_lotsOfCustomers"
            targetProfilePath = os.path.join(targetBasePath, itemName) + ".profile"
            targetReportPath = os.path.join(targetBasePath, itemName) + ".txt"
            _tools.mkdirs(os.path.dirname(targetReportPath))
            cProfile.run("from tests import test_performance; test_performance._buildAndValidateManyCustomers()", targetProfilePath)
            targetReportFile = io.open(targetReportPath, "w", encoding='utf-8')
            try:
                stats = pstats.Stats(targetProfilePath, stream=targetReportFile)
                stats.sort_stats("cumulative").print_stats("cutplace", 20)
            finally:
                targetReportFile.close()
        else:  # pragma: no cover
            _buildAndValidateManyCustomers()


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    unittest.main()
