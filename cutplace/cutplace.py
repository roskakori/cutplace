#!/usr/bin/env python
"""
Cutplace - Validate flat data according to an interface control document.
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
import codecs
import csv
import encodings
import glob
import interface
import logging
import optparse
import platform
import os
import sys
import tools
import traceback
import version
import web

DEFAULT_ICD_ENCODING = "ascii"

def _openForWriteUsingUtf8(targetPath):
    assert targetPath is not None
    return codecs.open(targetPath, encoding="utf-8", mode="w")

class ExitQuietlyOptionError(optparse.OptionError):
    """
    Pseudo error to indicate the program should exit quietly, for example when --help or --verbose
    was specified.
    """
    pass

class NoExitOptionParser(optparse.OptionParser):
    def exit(self, status=0, msg=None):
        if status:
            raise optparse.OptionError(msg, "")
        else:
            raise ExitQuietlyOptionError(msg, "")

    def error(self, msg):
        raise optparse.OptionError(msg, "")
    
    def print_version(self, file=None):
        # No super() due to old style class.
        optparse.OptionParser.print_version(self, file)
        if self.version:
            print >> file, "Python %s, %s" % (tools.pythonVersion(), tools.platformVersion()) 

class CutplaceValidationEventListener(interface.ValidationEventListener):
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

    def acceptedRow(self, row):
        self.acceptedRowCount += 1
        if self.acceptedFile is None:
            self.log.info("accepted: %r" % row)
        else:
            # Write to a csv.writer.
            self.acceptedFile.writerow(row)
    
    def rejectedRow(self, row, error):
        self.rejectedRowCount += 1
        rowText = "items: %r" % row
        errorText = "field error: %s" % error
        if self.rejectedFile is None:
            self.log.error(rowText)
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (rowText, os.linesep))
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))
    
    def checkAtEndFailed(self, error):
        errorText = "check at end failed: %s" % error
        self.checksAtEndFailedCount += 1
        if self.rejectedFile is None:
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))
    
class CutPlace(object):
    """
    Command line interface for CutPlace.
    """

    # Mapping for value of --log to logging level
    _LOG_LEVEL_MAP = {"debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL}

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
        
        usage = """
  %prog [options] ICD-FILE
    validate interface control document in ICD-FILE
  %prog [options] ICD-FILE DATA-FILE(S)
    validate DATA-FILE(S) according to rules specified in ICD-FILE
  %prog --web [options]
    launch web server providing a web interface for validation"""

        parser = NoExitOptionParser(usage=usage, version="%prog " + version.VERSION_TAG)
        parser.set_defaults(icdEncoding=DEFAULT_ICD_ENCODING, isLogTrace=False, isOpenBrowser=False, logLevel="warning", port=web.DEFAULT_PORT)
        parser.add_option("--list-encodings", action="store_true", dest="isShowEncodings", help="show list of available character encodings and exit")
        validationGroup = optparse.OptionGroup(parser, "Validation options", "Specify how to validate data and how to report the results")
        validationGroup.add_option("-e", "--icd-encoding", metavar="ENCODING", dest="icdEncoding",
                                   help="character encoding to use when reading the ICD (default: %default)")
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
        loggingGroup.add_option("--log", metavar="LEVEL", type="choice", choices=CutPlace._LOG_LEVEL_MAP.keys(), dest="logLevel", help="set log level to LEVEL (default: %default)")
        loggingGroup.add_option("-t", "--trace", action="store_true", dest="isLogTrace", help="include Python stack in error messages related to data")
        parser.add_option_group(loggingGroup)
        
        (self.options, others) = parser.parse_args(argv)

        self._log.setLevel(CutPlace._LOG_LEVEL_MAP[self.options.logLevel])
        self.icdEncoding = self.options.icdEncoding
        self.isLogTrace = self.options.isLogTrace
        self.isOpenBrowser = self.options.isOpenBrowser
        self.isShowEncodings = self.options.isShowEncodings
        self.isWebServer = self.options.isWebServer
        self.port = self.options.port
        self.isSplit = self.options.isSplit

        if not self.isShowEncodings and not self.isWebServer:
            if len(others) >= 1:
                icdPath = others[0]
                try:
                    self.setIcdFromFile(icdPath)
                except EnvironmentError, error:
                    raise IOError("cannot read ICD file %r: %s" % (icdPath, error))
                if len(others) >= 2:
                    self.dataToValidatePaths = others[1:]
            else:
                parser.error("file containing ICD must be specified")

        self._log.debug("cutplace " + version.VERSION_TAG)
        self._log.debug("options=" + str(self.options))
        self._log.debug("others=" + str(others))

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
                validationSplitListener = CutplaceValidationEventListener(tools.UnicodeCsvWriter(acceptedCsvFile), rejectedTextFile)
            else:
                validationSplitListener = CutplaceValidationEventListener()
            try:
                self.icd.validate(dataFilePath, validationSplitListener)
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
            
def main(options):
    """
    Main routine that might raise errors but won't `sys.exit()`.
    
    `options` is string array containing the command line options to process, for example
    `sys.argv[1:]`.
    """
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)

    cutPlace = CutPlace()
    cutPlace.setOptions(options)
    if cutPlace.isShowEncodings:
        cutPlace._printAvailableEncodings()
    elif cutPlace.isWebServer:
        web.main(cutPlace.port, cutPlace.isOpenBrowser)
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
            sys.exit(1)

def _exitWithError(exitCode, error):
    """
    Print `error` and `sys.exit()` with `exitCode`.
    """
    assert exitCode is not None
    assert exitCode > 0
    assert error is not None
    
    sys.stderr.write("%s%s" % (error, os.linesep))
    sys.exit(exitCode)
    
def mainForScript():
    """
    Main routine that reports errors in options to `sys.stderr` and does `sys.exit()`.
    """
    try:
        main(sys.argv[1:])
    except EnvironmentError, error:
        _exitWithError(3, error)
    except tools.CutplaceUnicodeError, error:
        _exitWithError(1, error)
    except tools.CutplaceError, error:
        _exitWithError(1, "cannot process Excel format: %s" % error)
    except optparse.OptionError, error:
        if not isinstance(error, ExitQuietlyOptionError):
            _exitWithError(2, "cannot process command line options: %s" % error)
    except optparse.OptionError, error:
        if not isinstance(error, ExitQuietlyOptionError):
            _exitWithError(2, "cannot process command line options: %s" % error)
    except Exception, error:
        traceback.print_exc()
        _exitWithError(4, "cannot handle unexpected error: %s" % error)
        
if __name__ == '__main__':
    mainForScript()
