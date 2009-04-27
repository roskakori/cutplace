#!/usr/bin/env python
"""Cutplace - Validate flat data according to an interface control document."""
# Copyright (C) 2009 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import encodings
import glob
import interface
import logging
import optparse
import platform
import os
import server
import sys
import tools
import version

class ExitQuietlyOptionError(optparse.OptionError):
    """Pseudo error to indicate the program should exit quietly, for example when --help or --verbose was
    specified."""
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

class CutplaceIcdEventListener(interface.IcdEventListener):
    """
    Listener for ICD events that writes accepted and rejected rows to the files specified in the
    command line options.
    """
    def __init__(self, acceptedCsvFile, rejectedTextFile):
        self.acceptedFile = acceptedCsvFile
        self.rejectedFile = rejectedTextFile
        self.log = logging.getLogger("cutplace")

    def acceptedRow(self, row):
        if self.acceptedFile is None:
            self.log.info("accepted: %r" % row)
        else:
            # Write to a csv.writer.
            self.acceptedFile.write(row)
    
    def rejectedRow(self, row, error):
        rowText = "items: %r" % row
        errorText = "field error: %s" % str(error)
        if self.rejectedFile is None:
            self.log.error(rowText)
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (rowText, os.linesep))
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))
    
    def checkAtRowFailed(self, row, error):
        rowText = "items: %r" % row
        errorText = "field error: %s" % str(error)
        if self.rejectedFile is None:
            self.log.error(rowText)
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (rowText, os.linesep))
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))
    
    def checkAtEndFailed(self, error):
        errorText = "check at end failed: %s" % str(error)
        if self.rejectedFile is None:
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))
    
    def dataFormatFailed(self, error):
        errorText = "data format error: %s" % str(error)
        if self.rejectedFile is None:
            self.log.error(errorText)
        else:
            # Write to a text file.
            self.rejectedFile.write("%s%s" % (errorText, os.linesep))

class CutPlace(object):
    """Command line interface for CutPlace."""

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
        self.icdPath = None
        self.dataToValidatePaths = None

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

        parser = NoExitOptionParser(usage=usage, version="%prog " + version.VERSION_NUMBER)
        parser.set_defaults(icdEncoding="iso-8859-1", isLogTrace=False, isOpenBrowser=False, logLevel="info", port=server.DEFAULT_PORT)
        parser.add_option("--list-encodings", action="store_true", dest="isShowEncodings", help="show list of available character encodings and exit")
        validationGroup = optparse.OptionGroup(parser, "Validation options", "Specify how to validate data and how to report the results")
        validationGroup.add_option("-e", "--icd-encoding", metavar="ENCODING", dest="icdEncoding", help="character encoding to use when reading the ICD (default: %default)")
        # TODO: validationGroup.add_option("-a", "--accepted", metavar="FILE", dest="pathForAcceptedRows", help="path for CSV file with accepted rows (default: log.info)")
        # TODO: validationGroup.add_option("-r", "--rejected", metavar="FILE", dest="pathForRejectedRows", help="path for row text file with rejected rows (default: log.error")
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
        self.isLogTrace = self.options.isLogTrace
        self.isOpenBrowser = self.options.isOpenBrowser
        self.isShowEncodings = self.options.isShowEncodings
        self.isWebServer = self.options.isWebServer
        self.port = self.options.port
        # TODO: self.pathForAcceptedRows = self.options.pathForAcceptedRows
        # TODO: self.pathForRejectedRows = self.options.pathForRejectedRows

        if not self.isShowEncodings and not self.isWebServer:
            if len(others) >= 1:
                self.setIcdFromFile(others[0])
                if len(others) >= 2:
                    self.dataToValidatePaths = others[1:]
            else:
                parser.error("file containing ICD  must be specified")

        self._log.debug("cutplace " + version.VERSION_TAG)
        self._log.debug("options=" + str(self.options))
        self._log.debug("others=" + str(others))

    def validate(self):
        assert self.icd is not None
        
        for dataFilePath in self.dataToValidatePaths:
            
            self.icd.validate(dataFilePath)
            
    def setIcdFromFile(self, newIcdPath):
        assert newIcdPath is not None
        newIcd = interface.InterfaceControlDocument()
        if self.options is not None:
            newIcd.logTrace = self.options.isLogTrace
        newIcd.read(newIcdPath)
        self.icd = newIcd 
        self.interfaceSpecificationPath = newIcdPath
        
    def _printAvailableEncodings(self):
        for encoding in self._encodingsFromModuleNames():
            if encoding != "__init__":
                print encoding

    def _encodingsFromModuleNames(self):
        # Base on sample code by Peter Otten.
        encodingsModuleFilePath = os.path.dirname(encodings.__file__)
        for filePath in glob.glob(os.path.join(encodingsModuleFilePath, "*.py")):
            fileName = os.path.basename(filePath)
            yield os.path.splitext(fileName)[0]
            
def main():
    """
    Main routine that might raise errors but won't sys.exit().
    """
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)

    cutPlace = CutPlace()
    cutPlace.setOptions(sys.argv[1:])
    if cutPlace.isShowEncodings:
        cutPlace._printAvailableEncodings()
    elif cutPlace.isWebServer:
        server.main(cutPlace.port, cutPlace.isOpenBrowser)
    elif cutPlace.dataToValidatePaths:
        for path in cutPlace.dataToValidatePaths:
            listener = CutplaceIcdEventListener(None, None)
            cutPlace.icd.addIcdEventListener(listener)
            try:
                cutPlace.icd.validate(path)
            finally:
                cutPlace.icd.removeIcdEventListener(listener)
                

def mainForScript():
    """
    Main routine that reports errors in options and does sys.exit().
    """
    try:
        main()
    except optparse.OptionError, message:
        if not isinstance(sys.exc_info()[1], ExitQuietlyOptionError):
            sys.stderr.write("cannot process command line options: %s%s" % (message, os.linesep))
            sys.exit(1)
    
if __name__ == '__main__':
    mainForScript()
