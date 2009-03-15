"""Interface control document (IDC) describing all aspects of a data driven interface."""
import csv
import fields
import logging
import parsers
import sys
import tools
import types

class DataFormat(object):
    """Properties from "Data format" section of ICD."""
    def __init__(self):
        self.KEY_ALLOWED = "allowed"
        self.KEY_ENCODING = "encoding"
        self.KEY_DECIMAL_SEPARATOR = "decimalSeparator"
        self.KEY_ITEM_SEPARATOR = "itemSeparator"
        self.KEY_LINE_SEPARATOR = "lineSeparator"
        self.KEY_DECIMAL_SEPARATOR = "decimalSeparator"
        self.KEY_THOUSANDS_SEPARATOR = "thousandsSeparator"
        self.KEY_FORMAT = "format"
        self.VALID_KEYS = [
                           self.KEY_ALLOWED,
                           self.KEY_DECIMAL_SEPARATOR,
                           self.KEY_ENCODING,
                           self.KEY_ITEM_SEPARATOR,
                           self.KEY_LINE_SEPARATOR,
                           self.KEY_THOUSANDS_SEPARATOR,
                           self.KEY_FORMAT
                           ]
        self.TYPE_CSV = "csv"
        self.VALID_TYPES = [
                            self.TYPE_CSV
                            ]
        self._log = logging.getLogger("cutplace")
        self.reset()

    def reset(self):
        self.allowed = None
        self.encoding = None
        self.decimaleSeparator = None
        self.thousandsSeparator = None
        self.format = None
        self.lineSeparator = parsers.AUTO
        self.itemSeparator = parsers.AUTO

    def set(self, key, value):
        """Set property key to value."""
        assert key is not None
        actualKey = tools.camelized(key, True)
        if not actualKey in self.VALID_KEYS:
            raise LookupError("data format key is %s but must be one of: %s" % (repr(actualKey), str(self.VALID_KEYS)))
        if value is None:
            actualValue = None
        else:
            actualValue = value.strip()
            if actualValue == "":
                actualValue = None
            if actualValue is not None:
                if actualKey == self.KEY_FORMAT:
                    if not actualValue.lower() in self.VALID_TYPES:
                        raise LookupError("data format type is \"%s\" but must be one of: %s" % (str(value), str(self.VALID_TYPES)))
        self._log.debug("set %s to \"%s\"" % (actualKey, str(actualValue)))
        setattr(self, actualKey, value)
        
    def lineSeparatorForDialect(self):
        # TODO: Unify line separator in IDC DataFormat and parsers.
        lineSeparator = self.lineSeparator.lower()
        if lineSeparator == "cr":
            result = parsers.CR
        elif lineSeparator == "crlf":
            result = parsers.CRLF
        elif lineSeparator == "lf":
            result = parsers.LF
        else:
            raise ValueError("lineSeparator=" + repr(lineSeparator))
        return result


class InterfaceDescription(object):
    """Model of the data driven parts of an Interface Control Document (ICD)."""
    def __init__(self):
        self.EMPTY_INDICATOR = "x"
        self.ID_CONSTRAINT = "c"
        self.ID_DATA_FORMAT = "d"
        self.ID_FIELD_RULE = "f"
        self.VALID_IDS = [self.ID_CONSTRAINT, self.ID_DATA_FORMAT, self.ID_FIELD_RULE]
        self._log = logging.getLogger("cutplace")
        self.dataFormat = DataFormat()
        self.fieldNames = []
        self.fieldFormats = []
        self.fieldNameToFormatMap = {}
    
    def _createFieldFormatClass(self, fieldType):
        assert fieldType is not None
        assert fieldType
        
        lastDotIndex = fieldType.rfind(".")
        if lastDotIndex >= 0:
            # FIXME: Detect and report errors for  cases ".class" and "module.".
            moduleName = fieldType[0:lastDotIndex]
            className = fieldType[lastDotIndex + 1:]
            module = __import__(moduleName)
        else:
            moduleName = "fields"
            className = fieldType
            module = sys.modules[moduleName]
        className += "FieldFormat"
        self._log.debug("create from " + str(moduleName) + " class " + className)
        try:
            result = getattr(module, className)
        except AttributeError:
            raise LookupError("cannot find field format: %s" % (str(fieldType)))
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
            raise IndexError("data format line (marked with %s) must contain at least 2 columns" % (repr(self.ID_DATA_FORMAT)))

    def addFieldFormat(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 2:
            fieldName = items[0].strip()
            if not fieldName:
                raise ValueError("field name must not be empty")
            fieldType = items[1].strip()
            fieldIsAllowedToBeEmpty = False
            if itemCount >= 3:
                fieldIsAllowedToBeEmptyText = items[2].strip().lower()
                if fieldIsAllowedToBeEmptyText == self.EMPTY_INDICATOR:
                    fieldIsAllowedToBeEmpty = True
                elif fieldIsAllowedToBeEmptyText:
                    raise ValueError("Mark for empty field is %s but must be %s" % (repr(fieldIsAllowedToBeEmptyText), repr(self.EMPTY_INDICATOR)))
                if itemCount >= 4:
                    fieldLength = fields.parsedLongRange("length", items[3])
                    if itemCount >= 5:
                        fieldRule = items[4].strip()
                        if not fieldRule:
                            fieldRule = None
            else:
                fieldRule = None
            fieldClass = self._createFieldFormatClass(fieldType);
            self._log.debug("create field: %s(%s, %s, %s)" % (str(fieldClass), str(fieldName), str(fieldType), str(fieldRule)))
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            fieldFormat.__init__(fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            if not self.fieldNameToFormatMap.has_key(fieldName):
                self.fieldNames.append(fieldName)
                self.fieldFormats.append(fieldFormat)
                self.fieldNameToFormatMap[fieldName] = fieldFormat
                self._log.info("defined field: %s: %s" % (fieldName, repr(fieldFormat)))
            else:
                raise LookupError("name must be used for only one field: %s" % (fieldName))
        else:
            raise IndexError("field format line (marked with %s) must contain at least 3 columns" % (repr(self.ID_FIELD_RULE)))
        
    def read(self, icdFilePath):
        # TODO: Allow to specify encoding.
        needsOpen = isinstance(icdFilePath, types.StringTypes)
        if needsOpen:
            icdFile = open(icdFilePath, "rb")
        else:
            icdFile = icdFilePath
        try:
            dialect = parsers.DelimitedDialect()
            dialect.lineDelimiter = parsers.AUTO
            dialect.itemDelimiter = parsers.AUTO
            dialect.quoteChar = "\""
            dialect.escapeChar = "\""
            parser = parsers.DelimitedParser(icdFile, dialect)
            reader = parsers.parserReader(parser)
            for row in reader:
                lineNumber = parser.lineNumber
                self._log.debug("parse icd line%5d: %s" % (lineNumber, str(row)))
                if len(row) >= 1:
                    rowId = str(row[0]).lower() 
                    if rowId == self.ID_CONSTRAINT:
                        pass
                    elif rowId == self.ID_DATA_FORMAT:
                        self.addDataFormat(row[1:])
                    elif rowId == self.ID_FIELD_RULE:
                        self.addFieldFormat(row[1:])
                    elif rowId.strip():
                        raise ValueError("first row in line %d is %s but must be empty or one of: %s" % (lineNumber, repr(row[0]), str(self.VALID_IDS)))
        finally:
            if needsOpen:
                icdFile.close()
            
    def validate(self, dataFileToValidatePath):
        """Validate that all lines and items in dataFileToValidatePath conform to this interface."""
        assert dataFileToValidatePath is not None
        self._log.info("validate \"%s\"" % (dataFileToValidatePath))
        
        # TODO: Clean up lower(), it should be called at a more appropriate place such as a property setter.
        if self.dataFormat.format.lower() == self.dataFormat.TYPE_CSV:
            dataFile = open(dataFileToValidatePath)
            try:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = self.dataFormat.lineSeparatorForDialect()
                dialect.itemDelimiter = self.dataFormat.itemSeparator
                # FIXME: Obtain quote char from ICD.
                dialect.quoteChar = "\""
                reader = parsers.delimitedReader(dataFile, dialect)
                for row in reader:
                    try:
                        itemIndex = 0
                        while itemIndex < len(row):
                            item = row[itemIndex]
                            fieldFormat = self.fieldFormats[itemIndex]
                            fieldFormat.validateEmpty(item)
                            fieldFormat.validateLength(item)
                            fieldFormat.validate(item)
                            itemIndex += 1
                        if itemIndex != len(row):
                            raise fields.FieldValueError("unexpected data must be removed beginning at item %d" % (itemIndex))
                        self._log.info("accepted: " + str(row))
                    except:
                        self._log.error("rejected: " + str(row), exc_info=1)
            finally:
                dataFile.close()
        else:
            raise NotImplementedError("data format:" + str(self.dataFormat.type))
