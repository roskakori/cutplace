"""
Development reports for cutplace.
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
import optparse
import os
import unittest

import _tools

_log = logging.getLogger("cutplace.dev_reports")

try:
    import cProfile
    import pstats
except ImportError, error:
    _log.warning(u"some developer reports will not work: %s", error)


def _testPerformance():
    """
    Run performance test.
    """
    import test_performace
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_performace.PerformanceTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


def _getSourceFolder():
    return "cutplace"


def _listdirPythonSource():
    return _tools.listdirMatching(_getSourceFolder(), ".*\\.py")


def _addToKeyList(targetMap, key, valueToAdd):
    if key in targetMap:
        targetMap[key].append(valueToAdd)
    else:
        targetMap[key] = [valueToAdd]


def createProfilerReport(targetBasePath):
    assert targetBasePath is not None

    itemName = "profile_lotsOfCustomers"
    targetProfilePath = os.path.join(targetBasePath, itemName) + ".profile"
    targetReportPath = os.path.join(targetBasePath, itemName) + ".txt"
    try:
        cProfile.run("_testPerformance()", targetProfilePath)
    except NameError:
        # HACK: Use explicit module prefix when run from setup.py.
        cProfile.run("dev_reports._testPerformance()", targetProfilePath)
    targetReportFile = open(targetReportPath, "w")
    try:
        stats = pstats.Stats(targetProfilePath, stream=targetReportFile)
        stats.sort_stats("cumulative").print_stats("cutplace", 20)
    finally:
        targetReportFile.close()


def createReports(targetFolder):
    assert targetFolder is not None

    _tools.mkdirs(targetFolder)
    createProfilerReport(targetFolder)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    logging.getLogger("cutplace.dev_reports").setLevel(logging.INFO)

    usage = u"usage: %prog FOLDER"
    parser = optparse.OptionParser(usage)
    options, others = parser.parse_args()
    if not others:
        parser.error(u"target folder for reports must be specified")
    baseFolder = others[0]
    createReports(baseFolder)
