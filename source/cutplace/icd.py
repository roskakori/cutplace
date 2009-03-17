"""Interface control document (IDC) describing all aspects of a data driven interface."""
import data
import fields
import logging
import parsers
import sys
import tools
import types

class InterfaceDescription(object):
    """Model of the data driven parts of an Interface Control Document (ICD)."""
    def __init__(self):
        # TODO: Move constants to class attributes.
        self.EMPTY_INDICATOR = "x"
        self.ID_CONSTRAINT = "c"
        self.ID_DATA_FORMAT = "d"
        self.ID_FIELD_RULE = "f"
        # TODO: Move to class attribute and rename to _VALID*
        self.VALID_IDS = [self.ID_CONSTRAINT, self.ID_DATA_FORMAT, self.ID_FIELD_RULE]
        self._log = logging.getLogger("cutplace")
        self.dataFormat = None
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
            if itemCount >= 2:
                value = items[1]
            else:
                # FIXME: Actually None must not be passed to most DataFormat.setXXX() methods.
                value = None
            if data.isFormatKey(key):
                if self.dataFormat is None:
                    self.dataFormat = data.createDataFormat(value)
                else:
                    raise data.DataFormatValueError("data format must be set only once, but has been set already to: %s" % (repr(self.dataFormat.getName())))
            else:
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
                            fieldRule = ""
            else:
                fieldRule = ""
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
                # TODO: Use FieldLookupError
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
        if self.dataFormat is None:
            raise data.DataFormatLookupError("ICD must contain a section describing the data format")
        if len(self.fieldFormats) == 0:
            # TODO: Use FieldLookupError
            raise fields.FieldValueError("ICD must contain a section describing at least one field format")
            
    def validate(self, dataFileToValidatePath):
        """Validate that all lines and items in dataFileToValidatePath conform to this interface."""
        assert self.dataFormat is not None
        assert dataFileToValidatePath is not None
        self._log.info("validate \"%s\"" % (dataFileToValidatePath))
        
        # TODO: Clean up lower(), it should be called at a more appropriate place such as a property setter.
        if self.dataFormat.getName() == data.FORMAT_CSV:
            dataFile = open(dataFileToValidatePath)
            try:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = self.dataFormat.getLineDelimiter()
                dialect.itemDelimiter = self.dataFormat.getItemDelimiter()
                # FIXME: Obtain quote char from ICD.
                dialect.quoteChar = "\""
                reader = parsers.delimitedReader(dataFile, dialect)
                for row in reader:
                    itemIndex = 0
                    try:
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
                        if isinstance(sys.exc_info()[1], (fields.FieldValueError)):
                            fieldName = self.fieldNames[itemIndex]
                            self._log.error("rejected: " + str(row))
                            self._log.error("  field %s: %s" % (repr(fieldName), sys.exc_value))
                        else:
                            self._log.error("rejected: " + str(row), exc_info=1)
            finally:
                dataFile.close()
        else:
            raise NotImplementedError("data format:" + str(self.dataFormat.getName()))
