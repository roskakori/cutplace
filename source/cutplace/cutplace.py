"""Cutplace - Tool to validate data according to an interface control document."""
import csv
import getopt
import logging
import re
import sys
import tools
import version

class FilePosition(object):
    """Reader position while parsing an ICD."""
    def __init__(self, line, column):
        self.line = line
        self.column = column

class DataFormat(object):
    """Properties from "Data format" section of ICD."""
    def __init__(self):
        self.KEY_ALLOWED = "allowed"
        self.KEY_ENCODING  = "encoding"
        self.KEY_DECIMAL_SEPARATOR = "decimalSeparator"
        self.KEY_ITEM_SEPARATOR = "itemSeparator"
        self.KEY_LINE_SEPARATOR = "lineSeparator"
        self.KEY_DECIMAL_SEPARATOR = "decimalSeparator"
        self.KEY_THOUSANDS_SEPARATOR = "thousandsSeparator"
        self.KEY_TYPE = "format"
        self.VALID_KEYS = [
                           self.KEY_ALLOWED, 
                           self.KEY_DECIMAL_SEPARATOR, 
                           self.KEY_ENCODING, 
                           self.KEY_ITEM_SEPARATOR, 
                           self.KEY_LINE_SEPARATOR, 
                           self.KEY_THOUSANDS_SEPARATOR, 
                           self.KEY_TYPE
                           ]
        self.TYPE_CSV = "csv"
        self.VALID_TYPES = [
                            self.TYPE_CSV
                            ]
        self.log = logging.getLogger("cutplace")
        self.reset()

    def reset(self):
        self.allowed = None
        self.encoding = None
        self.separator = None
        self.type = None

    def set(self, key, value):
        """Set property key to value."""
        assert key is not None
        actualKey = tools.camelized(key, True)
        if not actualKey in self.VALID_KEYS:
            raise LookupError("data format key is \"%s\" but must be one of: %s" %(actualKey, str(self.VALID_KEYS)))
        if value is None:
            actualValue = None
        else:
            actualValue = value.strip()
            if actualValue == "":
                actualValue = None
            if actualValue is not None:
                if actualKey == self.KEY_TYPE:
                    if not actualValue.lower() in self.VALID_TYPES:
                        raise LookupError("data format type is \"%s\" but must be one of: %s" %(str(value), str(self.VALID_TYPES)))
        self.log.debug("set %s to \"%s\"" %(actualKey, str(actualValue)))
        setattr(self, actualKey, value)

class FieldValueError(ValueError):
    """Error raised when AbstractFieldFormat.validate detects an error."""

class AbstractFieldFormat(object):
    """Description of a field."""
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        assert fieldName is not None
        assert fieldName, "fieldName must not be empty"
        assert rule is not None
        assert isAllowedToBeEmpty is not None

        self.fieldName = fieldName
        self.isAllowedToBeEmpty = isAllowedToBeEmpty
        self.rule = rule
    
    def validate(self, value):
        """Validate that value complies with field description. If not, raise FieldValueError."""
        raise NotImplementedError

class ChoiceFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        self.choices = []
        for choice in rule.lower().split(","):
            self.choices.append(choice.trim())
        if not choices:
            raise ValueError("at least one choice must be specified for a \"Choice\" field")
    
    def validate(self, value):
        if value.lower() not in sefl.choices:
            raise FieldValueError("value is \"%s\" but must be one of: %s" %(value, str(choices)))
    
class IntegerFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        self.regex = re.compile(rule)
   
    def validate(self, value):
        try:
            longValue = long(value)
        except ValueError:
            raise FieldValueError("value must be an integer number: \"%s\"" %(str(value)))
        if self.rule:
            # TODO: Validate range
            pass 

class DateFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
   
    def validate(self, value):
        # TODO: Validate Date
        pass

class RegExFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)

    def validate(self, value):
        if not self.regex.match(value):
            raise FieldValueError("value \"%s\" must match regular expression: \"%s\"" %(str(value), str(self.rule)))

class TextFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        self.regex = re.compile(rule)
   
    def validate(self, value):
        # TODO: Validate Text
        pass

class InterfaceDescription(object):
    """Model the data driven parts of an Interface Control Document (ICD)."""
    def __init__(self):
        self.EMPTY_INDICATOR  = "x"
        self.ID_CONSTRAINT = "c"
        self.ID_DATA_FORMAT = "d"
        self.ID_FIELD_RULE = "f"
        self.VALID_IDS = [self.ID_CONSTRAINT, self.ID_DATA_FORMAT, self.ID_FIELD_RULE]
        self.log = logging.getLogger("cutplace")
        self.dataFormat = DataFormat()
        self.log = logging.getLogger("cutplace")
    
    def _createFieldFormatClass(self, fieldType):
        assert fieldType is not None
        assert fieldType
        
        lastDotIndex = fieldType.rfind(".")
        if lastDotIndex >= 0:
            # FIXME: Detect and report errors for  cases ".class" and "module.".
            moduleName = fieldType[0:lastDotIndex]
            className = fieldType[lastDotIndex+1:]
            module = __import__(moduleName)
        else:
            moduleName = __name__
            className = fieldType
            module = sys.modules[__name__]
        className += "FieldFormat"
        log.debug("create from "  + str(moduleName) + " class " + className)
        try:
            result = getattr(module, className)
        except AttributeError:
            raise LookupError("cannot find field format: %s" %(str(fieldType)))
        return result

    def addDataFormat(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 1:
            key = items[0]
            if itemCount >= 3:
                value = items[1]
            else:
                value = None
            self.dataFormat.set(key, value)
        else:
            raise IndexError("data format line (marked with \"" + self.ID_DATA_FORMAT + "\") must contain at least 2 columns")

    def addFieldFormat(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 2:
            fieldName = items[0].strip()
            if not fieldName:
                raise ValueError("field name must not be empty")
            fieldType = items[1].strip()
            if itemCount >= 3:
                fieldRule = items[2].strip()
                if not fieldRule:
                    fieldRule = None
                if itemCount >= 4:
                    fieldIsAllowedToBeEmptyText = items[3].strip().lower()
                    if fieldIsAllowedToBeEmptyText == self.EMPTY_INDICATOR:
                        fieldIsAllowedToBeEmpty = True
                    elif fieldIsAllowedToBeEmptyText:
                        raise ValueError("Mark for empty field is \"%s\" but must be \"%s\"" %(fieldIsAllowedToBeEmptyText, self.EMPTY_INDICATOR))
            else:
                fieldRule = None
            fieldClass = self._createFieldFormatClass(fieldType);
            self.log.debug("create field: %s(%s, %s, %s)" %(str(fieldClass), str(fieldName), str(fieldType), str(fieldRule)))
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldRule, True)
        else:
            raise IndexError("field format line (marked with \"" + self.ID_FIELD_RULE + "\") must contain at least 3 columns")
        
    def read(self, icdFilePath):
        icdFile = open(icdFilePath, "rb")
        try:
            dialect = csv.Sniffer().sniff(icdFile.read(1024))
            icdFile.seek(0)
            reader = csv.reader(icdFile, dialect)
            for row in reader:
                lineNumber = reader.line_num
                self.log.debug("parse icd line%5d: %s" %(lineNumber, str(row)))
                if len(row) >= 1:
                    rowId = str(row[0]).lower() 
                    if rowId == self.ID_CONSTRAINT:
                        pass
                    elif rowId == self.ID_DATA_FORMAT:
                        self.addDataFormat(row[1:])
                    elif rowId == self.ID_FIELD_RULE:
                        self.addFieldFormat(row[1:])
                    elif rowId:
                        raise ValueError("first row in line %d is \"%s\" but must be empty or one of: %s" %(lineNumber, str(row[0]), str(self.VALID_IDS)))
        finally:
            icdFile.close()
            
    def validate(self, dataFileToValidatePath):
        """Validate that all lines and items in dataFileToValidatePath conform to this interface."""
        assert dataFileToValidatePath is not None
        self.log.info("validate \"%s\"" %(dataFileToValidatePath))
        if self.dataFormat.type == DataFormat.TYPE_CSV:
            dialect = csv.Dialect
            dataFile = open(dataFileToValidatePath)
            try:
                for items in csv.reader(dataFile, dialect):
                    pass
            finally:
                dataFile.close()
        else:
            raise NotImplementedError("data format:" + str(self.dataFormat.type))
    
                
# TODO: error handling for caller:
#        except csv.Error, e:
#            sys.exit('file %s, line %d: %s' % (filePath, reader.line_num, e))    

class CutPlace(object):
    """Command line interface for CutPlace."""

    def __init__(self):
        self.log = logging.getLogger("cutplace")
        self.reset()

        # Mapping for value of --log to logging level
        self.LEVELS = {'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL}

        # Options and shortcuts
        self.OPTION_HELP = "help"
        self.OPTION_HELP_TEXT = "--" + self.OPTION_HELP
        self.OPTION_LOG = "log"
        self.OPTION_LOG_TEXT = "--" + self.OPTION_LOG
        self.OPTION_VERSION = "version"
        self.OPTION_VERSION_TEXT = "--" + self.OPTION_VERSION
        self.SHORT_HELP = "h"
        self.SHORT_HELP_TEXT = "-" + self.SHORT_HELP
        
    def reset(self):
        """"Reset all options to their initial state so this CutPlace can be reused for another validation."""
        self.isShowHelp = False
        self.isShowVersion = False
        self.interfaceSpecificationPath = None
        self.dataToValidatePaths = None
        self.icd = None

    def setOptions(self, argv):
        """Reset options and set them again from argument list such as sys.argv[1:]."""
        assert argv is not None
        
        shortOptions = self.SHORT_HELP
        longOptions = [self.OPTION_HELP, self.OPTION_LOG + "=", self.OPTION_VERSION]
        options, others = getopt.getopt(sys.argv[1:], shortOptions, longOptions)

        for option, value in options:
            if option in (self.OPTION_HELP_TEXT, self.SHORT_HELP_TEXT):
                self.isShowHelp = True
            elif option in (self.OPTION_LOG_TEXT):
                optionLog = self.LEVELS.get(value)
                if optionLog is not None:
                    self.log.setLevel(optionLog)
                else:
                    raise getopt.GetoptError("value specified for " + option + " must be one of: " + str(sorted(LEVEL.keys)))
            elif option in (self.OPTION_VERSION_TEXT):
                self.isShowVersion = True
            else:
                raise NotImplementedError("option must be implemented: " + option)

        log.debug("cutplace " + version.VERSION_TAG)
        log.debug("options=" + str(options))
        log.debug("others=" + str(others))
    
        if not (self.isShowHelp or self.isShowVersion):
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
        newIcd = InterfaceDescription()
        newIcd.read(newIcdPath)
        self.icd = newIcd 
        self.interfaceSpecificationPath = newIcdPath
        
    def _printHeader(self):
        print "cutplace " + version.VERSION_TAG
    
    def _printUsage(self):
        INDENT = " " * 2
        self._printHeader()
        print "Usage:"
        print INDENT + "cutplace [options] interface-control-document"
        print INDENT + INDENT + "check syntax and semantic of interface control document"
        print INDENT + "cutplace [options] interface-control-document data-file(s)"
        print INDENT + INDENT + "validate that data-file conforms to interface control document"
        print "Options:"
        print INDENT + self.OPTION_HELP_TEXT + ", " + self.SHORT_HELP_TEXT + ": print usage information and exit"
        print INDENT + self.OPTION_LOG_TEXT + "={level}: set logging level to debug, info, warning, error or critical"
    
if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger("cutplace")
    log.setLevel(logging.INFO)

    cutPlace = CutPlace()
    cutPlace.setOptions(sys.argv[1:])
    if cutPlace.isShowHelp:
        cutPlace._printUsage()
    elif cutPlace.isShowVersion:
        cutPlace._printHeader()
    else:
        for path in cutPlace.dataToValidatePaths:
            log.info("validate %s according to %s" % (path, cutPlace.interfaceSpecificationPath))
