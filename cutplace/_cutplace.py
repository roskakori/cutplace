#!/usr/bin/env python
"""
Cutplace - Validate flat data according to an interface control document.
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
import codecs
import encodings
import glob
import logging
import optparse
import os
import sys
import xlrd

import interface
import tools
import version
import _tools
import _web

DEFAULT_ICD_ENCODING = "ascii"
DESCRIPTION = "validate data stored in CSV, PRN, ODS or Excel files"

_log = logging.getLogger("cutplace")


def _openForWriteUsingUtf8(targetPath):
    assert targetPath is not None
    return codecs.open(targetPath, encoding="utf-8", mode="w")


class _ExitQuietlyOptionError(optparse.OptionError):
    """
    Pseudo error to indicate the program should exit quietly, for example when --help or --verbose
    was specified.
    """
    pass


class _NoExitOptionParser(optparse.OptionParser):
    def exit(self, status=0, msg=None):
        if status:
            raise optparse.OptionError(msg, "")
        else:
            raise _ExitQuietlyOptionError(msg, "")

    def error(self, msg):
        raise optparse.OptionError(msg, "")

    def print_version(self, targetFile=None):
        # No super() due to old style class.
        optparse.OptionParser.print_version(self, targetFile)
        if self.version:
            print >> targetFile, "Python %s, %s" % (_tools.pythonVersion(), _tools.platformVersion())


class CutplaceValidationListener(interface.BaseValidationListener):
    """
    Listener for ICD events that writes accepted and rejected rows to the files specified in the
    command line options.
    """
    def __init__(self, acceptedCsvWriter=None, rejectedTextFile=None):
        self.acceptedFile = acceptedCsvWriter
        self.rejectedFile = rejectedTextFile
        self.acceptedRowCount = 0
        self.rejectedRowCount = 0
        self.checksAtEndFailedCount = 0
        self.log = logging.getLogger("cutplace")

    def acceptedRow(self, row, location):
        self.acceptedRowCount += 1
        if self.acceptedFile is None:
            self.log.info(u"accepted: %r", row)
        else:
            # Write to a csv.writer.
            self.acceptedFile.writerow(row)

    def rejectedRow(self, row, error):
        self.rejectedRowCount += 1
        rowText = "items: %r" % row
        errorText = "field error: %s" % error
        if self.rejectedFile is None:
            self.log.error(u"%s", rowText)
            self.log.error(u"%s", errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (rowText, os.linesep))
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))

    def checkAtEndFailed(self, error):
        errorText = "check at end failed: %s" % error
        self.checksAtEndFailedCount += 1
        if self.rejectedFile is None:
            self.log.error(u"%s", errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))


class CutPlace(object):
    """
    Command line interface for CutPlace.
    """
    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.options = None
        self.icd = None
        self.icdEncoding = DEFAULT_ICD_ENCODING
        self.icdPath = None
        self.isSplit = False
        self.dataToValidatePaths = None
        self.lastValidationWasOk = False

    def setOptions(self, argv):
        """Reset options and set them again from argument list such as sys.argv[1:]."""
        assert argv is not None

        usage = u"""
  cutplace [options] ICD-FILE
    validate interface control document in ICD-FILE
  cutplace [options] ICD-FILE DATA-FILE(S)
    validate DATA-FILE(S) according to rules specified in ICD-FILE
  cutplace --web [options]
    launch web server providing a web interface for validation"""

        parser = _NoExitOptionParser(usage=usage, version="%prog " + version.VERSION_TAG)
        parser.set_defaults(icdEncoding=DEFAULT_ICD_ENCODING, isLogTrace=False, isOpenBrowser=False, logLevel="warning", port=_web.DEFAULT_PORT)
        parser.add_option("--list-encodings", action="store_true", dest="isShowEncodings", help="show list of available character encodings and exit")
        validationGroup = optparse.OptionGroup(parser, "Validation options", "Specify how to validate data and how to report the results")
        validationGroup.add_option("-e", "--icd-encoding", metavar="ENCODING", dest="icdEncoding",
                help="character encoding to use when reading the ICD (default: %default)")
        validationGroup.add_option("-P", "--plugins", metavar="FOLDER", dest="pluginsFolderPath",
                help="folder to scan for plugins (default: %default)")
        validationGroup.add_option("-s", "--split", action="store_true", dest="isSplit",
                help="split data in a CSV file containing the accepted rows and a raw text file "
                + "containing rejected rows with both using UTF-8 as character encoding")
        parser.add_option_group(validationGroup)
        webGroup = optparse.OptionGroup(parser, "Web options", "Provide a  GUI for validation using a simple web server")
        webGroup.add_option("-w", "--web", action="store_true", dest="isWebServer", help="launch web server")
        webGroup.add_option("-p", "--port", metavar="PORT", type="int", dest="port", help="port for web server (default: %default)")
        webGroup.add_option("-b", "--browse", action="store_true", dest="isOpenBrowser", help="open validation page in browser")
        parser.add_option_group(webGroup)
        loggingGroup = optparse.OptionGroup(parser, "Logging options", "Modify the logging output")
        loggingGroup.add_option("--log", metavar="LEVEL", type="choice", choices=_tools.LogLevelNameToLevelMap.keys(), dest="logLevel", help="set log level to LEVEL (default: %default)")
        loggingGroup.add_option("-t", "--trace", action="store_true", dest="isLogTrace", help="include Python stack in error messages related to data")
        parser.add_option_group(loggingGroup)

        (self.options, others) = parser.parse_args(argv[1:])

        self._log.setLevel(_tools.LogLevelNameToLevelMap[self.options.logLevel])
        self.icdEncoding = self.options.icdEncoding
        self.isLogTrace = self.options.isLogTrace
        self.isOpenBrowser = self.options.isOpenBrowser
        self.isShowEncodings = self.options.isShowEncodings
        self.isWebServer = self.options.isWebServer
        self.port = self.options.port
        self.isSplit = self.options.isSplit

        if self.options.pluginsFolderPath is not None:
            interface.importPlugins(self.options.pluginsFolderPath)

        if not self.isShowEncodings and not self.isWebServer:
            if len(others) >= 1:
                icdPath = others[0]
                try:
                    self.setIcdFromFile(icdPath)
                except EnvironmentError, error:
                    raise IOError(u"cannot read ICD file %r: %s" % (icdPath, error))
                if len(others) >= 2:
                    self.dataToValidatePaths = others[1:]
            else:
                parser.error(u"file containing ICD must be specified")

        self._log.debug(u"cutplace %s", version.VERSION_TAG)
        self._log.debug(u"options=%s", self.options)
        self._log.debug(u"others=%s", others)

    def validate(self, dataFilePath):
        """
        Validate data stored in file `dataFilePath`.
        """
        assert dataFilePath is not None
        assert self.icd is not None

        self.lastValidationWasOk = False
        isWriteSplit = self.isSplit
        if isWriteSplit:
            splitTargetFolder, splitBaseName = os.path.split(dataFilePath)
            splitBaseName = os.path.splitext(dataFilePath)[0]
            acceptedCsvPath = os.path.join(splitTargetFolder, splitBaseName + "_accepted.csv")
            rejectedTextPath = os.path.join(splitTargetFolder, splitBaseName + "_rejected.txt")
            acceptedCsvFile = open(acceptedCsvPath, "w")
        try:
            if isWriteSplit:
                rejectedTextFile = _openForWriteUsingUtf8(rejectedTextPath)
                validationSplitListener = CutplaceValidationListener(_tools.UnicodeCsvWriter(acceptedCsvFile), rejectedTextFile)
            else:
                validationSplitListener = CutplaceValidationListener()
            try:
                self.icd.addValidationListener(validationSplitListener)
                try:
                    self.icd.validate(dataFilePath)
                finally:
                    self.icd.removeValidationListener(validationSplitListener)
                shortDataFilePath = os.path.basename(dataFilePath)
                acceptedRowCount = validationSplitListener.acceptedRowCount
                rejectedRowCount = validationSplitListener.rejectedRowCount
                checksAtEndFailedCount = validationSplitListener.checksAtEndFailedCount
                totalRowCount = acceptedRowCount + rejectedRowCount
                if rejectedRowCount + checksAtEndFailedCount == 0:
                    self.lastValidationWasOk = True
                    print "%s: accepted %d rows" % (shortDataFilePath, acceptedRowCount)
                else:
                    print "%s: rejected %d of %d rows. %d final checks failed." \
                         % (shortDataFilePath, rejectedRowCount, totalRowCount, checksAtEndFailedCount)
            finally:
                if isWriteSplit:
                    rejectedTextFile.close()
        finally:
            if isWriteSplit:
                acceptedCsvFile.close()

    def setIcdFromFile(self, newIcdPath):
        assert newIcdPath is not None
        newIcd = interface.InterfaceControlDocument()
        if self.options is not None:
            newIcd.logTrace = self.options.isLogTrace
        newIcd.read(newIcdPath, self.icdEncoding)
        self.icd = newIcd
        self.interfaceSpecificationPath = newIcdPath

    def _printAvailableEncodings(self):
        for encoding in self._encodingsFromModuleNames():
            if encoding != "__init__":
                print encoding

    def _encodingsFromModuleNames(self):
        # Based on sample code by Peter Otten.
        encodingsModuleFilePath = os.path.dirname(encodings.__file__)
        for filePath in glob.glob(os.path.join(encodingsModuleFilePath, "*.py")):
            fileName = os.path.basename(filePath)
            yield os.path.splitext(fileName)[0]


def process(argv=None):
    """
    Do whatever the command line options ``argv`` request. In case of error, raise an appropriate
    ``Exception``.

    Return 0 unless ``argv`` requested to validate one or more files and at least one of them
    contained rejected data. In this case, the result is 1.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    ``logging.basicConfig()``.
    """
    if argv is None:
        argv = sys.argv
    assert argv

    result = 0
    cutPlace = CutPlace()
    cutPlace.setOptions(argv)
    if cutPlace.isShowEncodings:
        cutPlace._printAvailableEncodings()
    else:
        if cutPlace.isWebServer:
            _web.main(cutPlace.port, cutPlace.isOpenBrowser)
        elif cutPlace.dataToValidatePaths:
            allValidationsOk = True
            for path in cutPlace.dataToValidatePaths:
                try:
                    cutPlace.validate(path)
                    if not cutPlace.lastValidationWasOk:
                        allValidationsOk = False
                except EnvironmentError, error:
                    raise EnvironmentError("cannot read data file %r: %s" % (path, error))
            if not allValidationsOk:
                result = 1
    return result


def main(argv=None):
    """
    Main routine that might raise errors but won't ``sys.exit()`` unless ``argv`` is broken.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    ``logging.basicConfig()``.
    """
    if argv is None:
        argv = sys.argv
    assert argv

    result = 1
    try:
        result = process(argv)
    except EnvironmentError, error:
        result = 3
        _log.error(u"%s", error)
    except tools.CutplaceUnicodeError, error:
        _log.error(u"%s", error)
    except tools.CutplaceError, error:
        _log.error(u"%s", error)
    except xlrd.XLRDError, error:
        _log.error(u"cannot process Excel format: %s", error)
    except _ExitQuietlyOptionError:
        # Raised by '--help', '--version', etc., so simply do nothing.
        pass
    except optparse.OptionError, error:
        result = 2
        _log.error(u"cannot process command line options: %s", error)
    except Exception, error:
        result = 4
        _log.exception(u"cannot handle unexpected error: %s", error)
    return result


def mainForScript():
    """
    Main routine that reports errors in options to ``sys.stderr`` and does ``sys.exit()``.
    """
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())

if __name__ == '__main__':
    mainForScript()
