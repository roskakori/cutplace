"""Interface control document (IDC) describing all aspects of a data driven interface."""
import checks
import data
import fields
import logging
import parsers
import sys
import tools
import types

class InterfaceDescription(object):
    """Model of the data driven parts of an Interface Control Document (ICD)."""
    _EMPTY_INDICATOR = "x"
    _ID_CONSTRAINT = "c"
    _ID_DATA_FORMAT = "d"
    _ID_FIELD_RULE = "f"
    _VALID_IDS = [_ID_CONSTRAINT, _ID_DATA_FORMAT, _ID_FIELD_RULE]
    
    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.dataFormat = None
        self.fieldNames = []
        self.fieldFormats = []
        self.fieldNameToFormatMap = {}
        self.checkDescriptions = {}
        # TODO: Add logTrace as property and let setter check for True or False.
        self.logTrace = False
    
    def _createClass(self, defaultModuleName, type, classNameAppendix, typeName):
        assert defaultModuleName
        assert type
        assert classNameAppendix
        assert typeName
        
        lastDotIndex = type.rfind(".")
        if lastDotIndex >= 0:
            # FIXME: Detect and report errors for  cases ".class" and "module.".
            moduleName = type[0:lastDotIndex]
            className = type[lastDotIndex + 1:]
            module = __import__(moduleName)
        else:
            moduleName = defaultModuleName
            className = type
            module = sys.modules[moduleName]
        className += classNameAppendix
        self._log.debug("create from " + str(moduleName) + " class " + className)
        try:
            result = getattr(module, className)
        except AttributeError:
            raise LookupError("cannot find %s: %s" % (typeName, str(type)))
        return result

    def _createFieldFormatClass(self, fieldType):
        return self._createClass("fields", fieldType, "FieldFormat", "field format")

    def _createCheckClass(self, checkType):
        return self._createClass("checks", checkType, "Check", "check")

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
                    raise data.DataFormatSyntaxError("data format must be set only once, but has been set already to: %r" % self.dataFormat.getName())
            else:
                self.dataFormat.set(key, value)
        else:
            raise data.DataFormatSyntaxError("data format line (marked with %r) must contain at least 2 columns" % InterfaceDescription._ID_DATA_FORMAT)

    def addFieldFormat(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 2:
            fieldName = items[0].strip()
            if not fieldName:
                raise fields.FieldSyntaxError("field name must not be empty")
            fieldType = items[1].strip()
            fieldIsAllowedToBeEmpty = False
            if itemCount >= 3:
                fieldIsAllowedToBeEmptyText = items[2].strip().lower()
                if fieldIsAllowedToBeEmptyText == InterfaceDescription._EMPTY_INDICATOR:
                    fieldIsAllowedToBeEmpty = True
                elif fieldIsAllowedToBeEmptyText:
                    raise fields.FieldSyntaxError("mark for empty field is %r but must be %r" % (fieldIsAllowedToBeEmptyText, InterfaceDescription._EMPTY_INDICATOR))
                if itemCount >= 4:
                    fieldLength = fields.parsedLongRange("length", items[3])
                    if itemCount >= 5:
                        fieldRule = items[4].strip()
                        if not fieldRule:
                            fieldRule = ""
            else:
                fieldRule = ""
            fieldClass = self._createFieldFormatClass(fieldType);
            self._log.debug("create field: %s(%r, %r, %r)" % (fieldClass.__name__, fieldName, fieldType, fieldRule))
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            fieldFormat.__init__(fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            if not self.fieldNameToFormatMap.has_key(fieldName):
                self.fieldNames.append(fieldName)
                self.fieldFormats.append(fieldFormat)
                # TODO: Rememer location where field format was defined to later include it in error message
                self.fieldNameToFormatMap[fieldName] = fieldFormat
                self._log.info("defined field: %s" % fieldFormat)
            else:
                raise fields.FieldSyntaxError("field name must be used for only one field: %s" % fieldName)
        else:
            raise fields.FieldSyntaxError("field format line (marked with %r) must contain at least 3 columns" % InterfaceDescription._ID_FIELD_RULE)
        
    def addCheck(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 2:
            checkDescription = items[0]
            checkType = items[1]
            if itemCount >= 3:
                checkRule = items[2]
            else:
                checkRule = ""
            self._log.debug("create check: %s(%r, %r)" % (checkType, checkDescription, checkRule))
            checkClass = self._createCheckClass(checkType)
            check = checkClass.__new__(checkClass, checkDescription, checkRule, self.fieldNames)
            check.__init__(checkDescription, checkRule, self.fieldNames)
            if not checkDescription in self.checkDescriptions:
                # TODO: Rememer location where check was defined to later include it in error message
                self.checkDescriptions[checkDescription] = check
            else:
                raise checks.CheckSyntaxError("check description must be used only once: %r" % (checkDescription)) 
        else:
            raise checks.CheckSyntaxError("check row (marked with %r) must contain at least 2 columns" % InterfaceDescription._ID_FIELD_RULE)

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
                    if rowId == InterfaceDescription._ID_CONSTRAINT:
                        self.addCheck(row[1:])
                    elif rowId == InterfaceDescription._ID_DATA_FORMAT:
                        self.addDataFormat(row[1:])
                    elif rowId == InterfaceDescription._ID_FIELD_RULE:
                        self.addFieldFormat(row[1:])
                    elif rowId.strip():
                        raise ValueError("first row in line %d is %r but must be empty or one of: %r" % (lineNumber, row[0], InterfaceDescription._VALID_IDS))
        finally:
            if needsOpen:
                icdFile.close()
        if self.dataFormat is None:
            raise data.DataFormatSyntaxError("ICD must contain a section describing the data format")
        if len(self.fieldFormats) == 0:
            raise fields.FieldSyntaxError("ICD must contain a section describing at least one field format")
            
    def validate(self, dataFileToValidatePath):
        """Validate that all lines and items in dataFileToValidatePath conform to this interface."""
        assert self.dataFormat is not None
        assert dataFileToValidatePath is not None
        self._log.info("validate \"%s\"" % (dataFileToValidatePath))
        
        # TODO: Clean up lower(), it should be called at a more appropriate place such as a property setter.
        if self.dataFormat.getName() == data.FORMAT_CSV:
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            if needsOpen:
                dataFile = open(dataFileToValidatePath, "rb")
            else:
                dataFile = dataFileToValidatePath
            try:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = self.dataFormat.getLineDelimiter()
                dialect.itemDelimiter = self.dataFormat.getItemDelimiter()
                # FIXME: Obtain quote char from ICD.
                dialect.quoteChar = "\""
                reader = parsers.delimitedReader(dataFile, dialect)
                rowNumber = 0
                for row in reader:
                    itemIndex = 0
                    rowNumber += 1
                    rowMap = {}
                    try:
                        # Validate all columns and collect their values in rowMap.
                        while itemIndex < len(row):
                            item = row[itemIndex]
                            fieldFormat = self.fieldFormats[itemIndex]
                            fieldFormat.validateEmpty(item)
                            fieldFormat.validateLength(item)
                            rowMap[fieldFormat.fieldName] = fieldFormat.validate(item) 
                            itemIndex += 1
                        if itemIndex != len(row):
                            raise fields.FieldValueError("unexpected data must be removed beginning at item %d" % (itemIndex))
                        # Validate row checks.
                        for description, check in self.checkDescriptions.items():
                            try:
                                check.checkRow(rowNumber, rowMap)
                            except checks.CheckError, message:
                                raise checks.CheckError("row check failed: %r: %s" % (check.description, message))
                        self._log.info("accepted: " + str(row))
                    except:
                        # Handle failed check and other errors.
                        # FIXME: Handle only errors based on CutplaceError here.
                        self._log.error("rejected: %s" % row)
                        if isinstance(sys.exc_info()[1], (fields.FieldValueError)):
                            fieldName = self.fieldNames[itemIndex]
                            basicReason = "  reason: field %r does not match format" % fieldName
                            if self.logTrace:
                                self._log.error(basicReason, exc_info=1)
                            else:
                                self._log.error("%s: %s" % (basicReason, sys.exc_info()[1]))
                        elif self.logTrace:
                            self._log.error("  reason: %r" % row, exc_info=1)
                        else:
                            self._log.error("  reason: %s" % sys.exc_info()[1])
                            
                # Validate checks at end of data.
                for description, check in self.checkDescriptions.items():
                    try:
                        self._log.debug("checkAtEnd: %r" % (check))
                        check.checkAtEnd()
                    except checks.CheckError, message:
                        raise CheckError("check at end of data failed: %r: %s" % (check.description, message))
            finally:
                if needsOpen:
                    dataFile.close()
        else:
            raise NotImplementedError("data format:" + str(self.dataFormat.getName()))
