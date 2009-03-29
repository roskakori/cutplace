"""Development reports for cutplace."""
import cgi
import coverage
import cProfile
import dev_colorize
import keyword
import logging
import optparse
import os
import pstats
import StringIO
import sys
import unittest

def _testLotsOfCustomers():
    import test_cutplace
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_cutplace.LotsOfCustomersTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

def createProfilerReport(targetBasePath):
    assert targetBasePath is not None
    
    itemName = "profile_lotsOfCustomers"
    targetProfilePath = os.path.join(targetBasePath, itemName) + ".profile"
    targetReportPath = os.path.join(targetBasePath, itemName) + ".txt"
    cProfile.run("_testLotsOfCustomers()", targetProfilePath)
    targetReportFile = open(targetReportPath, "w")
    try:
        stats = pstats.Stats(targetProfilePath, stream=targetReportFile)
        stats.sort_stats("cumulative").print_stats("cutplace", 20)
    finally:
        targetReportFile.close()

def createCoverageReport(targetBasePath):
    # Collect coverage data.
    print "collecting coverage data"
    coverage.erase()
    coverage.start()
    import tools
    modules = []
    # Note: in order for this to work the script must run from project folder.
    moduleFilesNames = tools.listdirMatching(os.path.join("source", "cutplace"), ".*\\.py")
    # Strip folder and extension from names
    moduleNames = [os.path.splitext(os.path.split(fileName)[1])[0] for fileName in moduleFilesNames]
    # FIXME: Figure out why we have duplicats and remove the hack below.
    moduleNames = set(moduleNames)
    # Remove "dev_" modules.
    moduleNames = [moduleName for moduleName in moduleNames if not moduleName.startswith("dev_")]
    moduleNames.sort()
    for moduleName in moduleNames:
        modules.append(__import__(moduleName))
    import test_all
    test_all.main()
    createProfilerReport(baseFolder)
    coverage.stop()

    # Create report.
    coverageHtml = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
    <head>
        <title>Cutplace Test Coverage</title>
    </head>
    <body>
        <h1>Cutplace Test Coverage</h1>
        <table>"""
        
    for module in modules:
        f, s, m, mf = coverage.analysis(module)
        coverageHtmlName = "coverage_" + os.path.basename(f) + ".html"
        targetHtmlPath = os.path.join(targetBasePath, coverageHtmlName)
        coverageHtml += "<tr><td><a href=\"%s\">%s</a></td>" % (coverageHtmlName, os.path.basename(f))
        reportStringIO = StringIO.StringIO()
        try:
            coverage.report(module, file=reportStringIO)
            reportStringIO.seek(0)
            moduleCoverageReport = reportStringIO.read()
            coverageHtml += "<td><pre>%s</pre></td></tr>" % cgi.escape(moduleCoverageReport)
        finally:
            reportStringIO.close() 
        print "write %r" % targetHtmlPath
        fo = file(targetHtmlPath, "wb")
        # colorization
        dev_colorize.colorize_file(f, outstream=fo, not_covered=mf)
        fo.close()
    coverageHtml += """        </table>
    </body>
</html>"""
    coverageHtmlFile = open(os.path.join(targetBasePath, "coverage.html"), "w")
    try:
        coverageHtmlFile.write(coverageHtml)
    finally:
        coverageHtmlFile.close()
    # print report on stdout
    # coverage.report(urllib2)
    # erase coverage data
    coverage.erase()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.WARNING)
    logging.getLogger("cutplace.dev_reports").setLevel(logging.INFO)

    usage = "usage: %prog FOLDER"
    parser = optparse.OptionParser(usage)
    options, others = parser.parse_args()
    if len(others) == 1:
        baseFolder = others[0]
        createCoverageReport(baseFolder)
    else:
        sys.stderr.write("%s%s" % ("target folder for reports must be specified", os.linesep))
        sys.exit(1)
        