"""Cutplace - Tool to validate data according to an interface control document."""
import encodings
import getopt
import glob
import icd
import logging
import platform
import os
import sys
import version

# Constants for options and shortcuts
_OPTION_HELP = "help"
_OPTION_HELP_TEXT = "--" + _OPTION_HELP
_OPTION_LIST_ENCODINGS = "listencodings"
_OPTION_LIST_ENCODINGS_TEXT = "--" + _OPTION_LIST_ENCODINGS
_OPTION_LOG = "log"
_OPTION_LOG_TEXT = "--" + _OPTION_LOG
_OPTION_VERSION = "version"
_OPTION_VERSION_TEXT = "--" + _OPTION_VERSION
_SHORT_HELP = "h"
_SHORT_HELP_TEXT = "-" + _SHORT_HELP
        
# Mapping for value of --log to logging level
_LOG_LEVEL_MAP = {"debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL}

class CutPlace(object):
    """Command line interface for CutPlace."""

    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.reset()

    def reset(self):
        """"Reset all options to their initial state so this CutPlace can be reused for another validation."""
        self.isShowEncodings = False
        self.isShowHelp = False
        self.isShowVersion = False
        self.interfaceSpecificationPath = None
        self.dataToValidatePaths = None
        self.icd = None

    def setOptions(self, argv):
        """Reset options and set them again from argument list such as sys.argv[1:]."""
        assert argv is not None
        
        shortOptions = _SHORT_HELP
        longOptions = [_OPTION_HELP, _OPTION_LIST_ENCODINGS, _OPTION_LOG + "=", _OPTION_VERSION]
        options, others = getopt.getopt(argv, shortOptions, longOptions)

        for option, value in options:
            if option in (_OPTION_HELP_TEXT, _SHORT_HELP_TEXT):
                self.isShowHelp = True
            elif option in (_OPTION_LIST_ENCODINGS_TEXT):
                self.isShowEncodings = True
            elif option in (_OPTION_LOG_TEXT):
                optionLog = _LOG_LEVEL_MAP.get(value)
                if optionLog is not None:
                    self._log.setLevel(optionLog)
                else:
                    raise getopt.GetoptError("value specified for " + option + " must be one of: " + str(sorted(LEVEL.keys)))
            elif option in (_OPTION_VERSION_TEXT):
                self.isShowVersion = True
            else:
                raise NotImplementedError("option must be implemented: " + option)

        self._log.debug("cutplace " + version.VERSION_TAG)
        self._log.debug("options=" + str(options))
        self._log.debug("others=" + str(others))
    
        if not (self.isShowEncodings or self.isShowHelp or self.isShowVersion):
            if len(others) >= 2:
                self.setIcdFromFile(others[0])
                self.dataToValidatePaths = others[1:]
            elif len(others) == 1:
                raise getopt.GetoptError("file(s) containing data to validate must be specified")
            else:
                assert len(others) == 0
                raise getopt.GetoptError("file containing interface specification and file(s) containing data to validate must be specified")

    def validate(self):
        for dataFilePath in self.dataToValidatePaths:
            self.icd.validate(dataFilePath)
            
    def setIcdFromFile(self, newIcdPath):
        assert newIcdPath is not None
        newIcd = icd.InterfaceDescription()
        newIcd.read(newIcdPath)
        self.icd = newIcd 
        self.interfaceSpecificationPath = newIcdPath
        
    def _printCutplaceVersion(self):
        print "cutplace " + version.VERSION_TAG
    
    def _printVersion(self):
        self._printCutplaceVersion()
        pythonVersion = platform.python_version()
        macVersion = platform.mac_ver()
        if (macVersion[0]):
            systemVersion = "Mac OS %s (%s)" % (macVersion[0], macVersion[2])
        else:
            systemVersion = platform.platform()
        print ("Python %s, %s" % (pythonVersion, systemVersion)) 
    def _printUsage(self):
        INDENT = " " * 2
        self._printCutplaceVersion()
        print "Copyright (C) Thomas Aglassinger 2009. Distributed under the GNU GPLv3 (or later)."
        print "For more information visit <http://cutplace.sourceforge.net/>."
        print
        print "Usage:"
        print INDENT + "cutplace [options] interface-control-document"
        print INDENT + INDENT + "check syntax and semantic of interface control document"
        print INDENT + "cutplace [options] interface-control-document data-file(s)"
        print INDENT + INDENT + "validate that data-file conforms to interface control document"
        print "Options:"
        print INDENT + _OPTION_LIST_ENCODINGS_TEXT + ": print list of available character encodings and exit"
        print INDENT + _OPTION_HELP_TEXT + ", " + _SHORT_HELP_TEXT + ": print usage information and exit"
        print INDENT + _OPTION_VERSION_TEXT + ": print version information and exit"
        print INDENT + _OPTION_LOG_TEXT + "={level}: set logging level to debug, info, warning, error or critical"
        
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
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)

    cutPlace = CutPlace()
    cutPlace.setOptions(sys.argv[1:])
    if cutPlace.isShowEncodings:
        cutPlace._printAvailableEncodings()
    elif cutPlace.isShowHelp:
        cutPlace._printUsage()
    elif cutPlace.isShowVersion:
        cutPlace._printVersion()
    else:
        for path in cutPlace.dataToValidatePaths:
            cutPlace.icd.validate(path)
    
if __name__ == '__main__':
    main()