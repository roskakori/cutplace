"""Cutplace - Tool to validate data according to an interface control document."""
import encodings
import glob
import interface
import logging
import optparse
import platform
import os
import sys
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
        optparse.OptionParser.print_version(self, file)
        # FIXME: Use: super(NoExitOptionParser, self).print_version(file)
        # But for some reason, this gives: TypeError: super() argument 1 must be type, not classobj
        if self.version:
            pythonVersion = platform.python_version()
            macVersion = platform.mac_ver()
            if (macVersion[0]):
                systemVersion = "Mac OS %s (%s)" % (macVersion[0], macVersion[2])
            else:
                systemVersion = platform.platform()
            print >> file, "Python %s, %s" % (pythonVersion, systemVersion) 


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
    validate DATA-FILE(S) according to rules specified in ICD-FILE"""

        parser = NoExitOptionParser(usage=usage, version="%prog " + version.VERSION_NUMBER)
        parser.set_defaults(logLevel="info")
        parser.add_option("--list-encodings", action="store_true", dest="isShowEncodings", help="print list of available character encodings and exit")
        parser.add_option("-t", "--trace", action="store_true", dest="isLogTrace", help="include Python stack in error messages related to data")
        parser.add_option("--log", metavar="LEVEL", type="choice", choices=CutPlace._LOG_LEVEL_MAP.keys(), dest="logLevel", help="set log level to LEVEL")
        (self.options, others) = parser.parse_args(argv)

        self.isShowEncodings = self.options.isShowEncodings

        if not self.isShowEncodings:
            if len(others) >= 1:
                self.setIcdFromFile(others[0])
                if len(others) >= 2:
                    self.dataToValidatePaths = others[1:]
            else:
                parser.error("file containing ICD  must be specified")

        self._log.setLevel(self.options.logLevel)
        
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
    elif cutPlace.dataToValidatePaths:
        for path in cutPlace.dataToValidatePaths:
            cutPlace.icd.validate(path)
    
if __name__ == '__main__':
    try:
        main()
    except optparse.OptionError, message:
        if not isinstance(sys.exc_info()[1], ExitQuietlyOptionError):
            sys.stderr.write("cannot process command line options: %s%s" % (message, os.linesep))
            sys.exit(1)
