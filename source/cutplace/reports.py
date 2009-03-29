"""Development reports for cutplace."""
import cProfile
import logging
import optparse
import os
import pstats
import sys
import test_cutplace
import test_all
import unittest

def _testLotsOfCustomers():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_cutplace.LotsOfCustomersTest)
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    logging.getLogger("cutplace").info("hello")
    unittest.TextTestRunner(verbosity=2).run(suite)

def createProfilerReport(targetBasePath):
    assert targetBasePath is not None
    
    # cProfile.run("test_all.main()", targetReportPath)
    itemName = "profile_lotsOfCustomers"
    targetProfilePath = os.path.join(targetBasePath, itemName) + ".profile"
    targetReportPath = os.path.join(targetBasePath, itemName) + ".txt"
    cProfile.run("_testLotsOfCustomers()", targetProfilePath)
    targetReportFile = open(targetReportPath, "w")
    try:
        stats = pstats.Stats(targetProfilePath, stream=targetReportFile)
        stats.sort_stats('cumulative').print_stats("cutplace", 20)
    finally:
        targetReportFile.close()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)

    usage = "usage: %prog FOLDER"
    parser = optparse.OptionParser(usage)
    options, others = parser.parse_args()
    if len(others) == 1:
        baseFolder = others[0]
        createProfilerReport(baseFolder)
    else:
        sys.stderr.write("%s%s" %("target folder for reports must be specified", os.linesep))
        sys.exit(1)
        