"""Interface control document (ICD) describing all aspects of a data driven interface."""
import checks
import codecs
import data
import fields
import logging
import os
import parsers
import range
import sys
import tools
import types

class IcdEventListener(object):
    """
    Listener to process events detected during parsing.
    """
    # FIXME: Add error positions: rowNumber, itemNumber, indexInItem
    def acceptedRow(self, row):
        pass
    
    def rejectedRow(self, row, errorMessage):
        pass
    
    def checkAtRowFailed(self, row, errorMessage):
        pass
    
    def checkAtEndFailed(self, errorMessage):
        pass
    
    def dataFormatFailed(self, errorMessage):
        pass

class IcdSyntaxError(tools.CutplaceError):
    """
    General syntax error in specification of the ICD.
    """

class InterfaceControlDocument(object):
    """
    Model of the data driven parts of an Interface Control Document (ICD).
    """
    _EMPTY_INDICATOR = "x"
    _ID_CHECK = "c"
    _ID_DATA_FORMAT = "d"
    _ID_FIELD_RULE = "f"
    _VALID_IDS = [_ID_CHECK, _ID_DATA_FORMAT, _ID_FIELD_RULE]
    # Header used by zipped ODS content.
    _ODS_HEADER = "PK\x03\x04"
    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.dataFormat = None
        self.fieldNames = []
        self.fieldFormats = []
        self.fieldNameToFormatMap = {}
        self.checkDescriptions = {}
        self.icdEventListeners = []
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
            try:
                module = sys.modules[moduleName]
            except KeyError:
                # TODO: Learn Python and remove hack to resolve "fields" vs "cutplace.fields" module names.
                # HACK: This is a workaround for the fact that during development for example the fields
                # module is referred to as "fields" while after installation it is "cutplace.fields".
                moduleName = "cutplace." + defaultModuleName
                module = sys.modules[moduleName]
        assert className
        assert moduleName
        className += classNameAppendix
        self._log.debug("create from " + str(moduleName) + " class " + className)
        try:
            result = getattr(module, className)
        except AttributeError:
            raise LookupError("cannot find %s: %s" % (typeName, str(type)))
        return result

    def _createFieldFormatClass(self, fieldType):
        assert fieldType
        return self._createClass("fields", fieldType, "FieldFormat", "field format")

    def _createCheckClass(self, checkType):
        assert checkType
        return self._createClass("checks", checkType, "Check", "check")

    def addDataFormat(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount >= 1:
            key = items[0]
            if itemCount >= 2:
                value = items[1]
            else:
                value = ""
            if data.isFormatKey(key):
                if self.dataFormat is None:
                    self.dataFormat = data.createDataFormat(value)
                else:
                    raise data.DataFormatSyntaxError("data format must be set only once, but has been set already to: %r" % self.dataFormat.getName())
            elif self.dataFormat is not None: 
                self.dataFormat.set(key, value)
            else:
                raise data.DataFormatSyntaxError("first data format property name is %r but must be %r" % (key, data.KEY_FORMAT))
        else:
            raise data.DataFormatSyntaxError("data format line (marked with %r) must contain at least 2 columns" % InterfaceControlDocument._ID_DATA_FORMAT)

    def addFieldFormat(self, items):
        """
        Add field as described by `items`. The meanings of the items are:
        
        0) field name
        1) field type
        2) optional: empty flag ("X"=field is allowed to be empty)
        3) optional: length ("lower:upper")
        4) optional: rule to validate field (depending on type)
        
        Further values in `items` are be ignored.
        
        Any errors detected result in a `fields.FieldSyntaxError`.
        """
        assert items is not None

        if self.dataFormat is None:
            raise data.DataFormatSyntaxError("data format must be specified before first field")

        # All these must have a value at the end.
        fieldName = None
        fieldType = None
        fieldRule = None
        
        itemCount = len(items)
        if itemCount >= 2:
            # Obtain field name.
            try:
                fieldName = tools.validatedPythonName("field name", items[0])
            except NameError, error:
                raise fields.FieldSyntaxError(str(error))
            # Obtain field type.
            try:
                fieldType = ""
                fieldTypeParts = items[1].split(".")
                for part in fieldTypeParts:
                    if fieldType:
                        fieldType += "."
                    fieldType += tools.validatedPythonName("field type part", part)
                if not fieldType:
                    raise fields.FieldSyntaxError("field type must not be empty")
            except NameError, error:
                raise fields.FieldSyntaxError(str(error))
            # Obtain "empty" flag. 
            fieldIsAllowedToBeEmpty = False
            if itemCount >= 3:
                fieldIsAllowedToBeEmptyText = items[2].strip().lower()
                if fieldIsAllowedToBeEmptyText == InterfaceControlDocument._EMPTY_INDICATOR:
                    fieldIsAllowedToBeEmpty = True
                elif fieldIsAllowedToBeEmptyText:
                    raise fields.FieldSyntaxError("mark for empty field must be %r or empty but is %r" 
                                                  % (InterfaceControlDocument._EMPTY_INDICATOR,
                                                     fieldIsAllowedToBeEmptyText))
                if itemCount >= 4:
                    fieldLength = items[3]
                    if itemCount >= 5:
                        fieldRule = items[4].strip()
                        if not fieldRule:
                            fieldRule = ""
            else:
                fieldRule = ""

            # Validate fixed fields.
            if self.dataFormat == data.FORMAT_FIXED:
                if fieldLength is None:
                    raise fields.FieldSyntaxError("field length must be specified with fixed data format")
                # FIXME: Validate that field length is fixed size.

            # Obtain class for field type.
            fieldClass = self._createFieldFormatClass(fieldType);
            self._log.debug("create field: %s(%r, %r, %r)" % (fieldClass.__name__, fieldName, fieldType, fieldRule))
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            fieldFormat.__init__(fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)

            # Validate that field name is unique.
            if not self.fieldNameToFormatMap.has_key(fieldName):
                self.fieldNames.append(fieldName)
                self.fieldFormats.append(fieldFormat)
                # TODO: Remember location where field format was defined to later include it in error message
                self.fieldNameToFormatMap[fieldName] = fieldFormat
                self._log.info("defined field: %s" % fieldFormat)
            else:
                raise fields.FieldSyntaxError("field name must be used for only one field: %s" % fieldName)
        else:
            raise fields.FieldSyntaxError("field format line (marked with %r) must contain at least 3 columns" % InterfaceControlDocument._ID_FIELD_RULE)

        assert fieldName
        assert fieldType
        assert fieldRule is not None
        
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
                # TODO: Remember location where check was defined to later include it in error message
                self.checkDescriptions[checkDescription] = check
            else:
                raise checks.CheckSyntaxError("check description must be used only once: %r" % (checkDescription)) 
        else:
            raise checks.CheckSyntaxError("check row (marked with %r) must contain at least 2 columns" % InterfaceControlDocument._ID_FIELD_RULE)

    def read(self, icdFilePath, encodingName="iso-8859-1"):
        needsOpen = isinstance(icdFilePath, types.StringTypes)
        if needsOpen:
            icdFile = open(icdFilePath, "rb")
        else:
            icdFile = icdFilePath
        try:
            icdHeader = icdFile.read(4)
            self._log.debug("icdHeader=%r" % icdHeader)
            icdFile.seek(0)
            isOds = icdHeader == InterfaceControlDocument._ODS_HEADER
            if isOds:
                parser = parsers.OdsParser(icdFile)
            else:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = parsers.AUTO
                dialect.itemDelimiter = parsers.AUTO
                dialect.quoteChar = "\""
                dialect.escapeChar = "\""
                parser = parsers.DelimitedParser(icdFile, dialect)
            reader = parsers.parserReader(parser)
            for row in reader:
                lineNumber = parser.lineNumber
                self._log.debug("parse icd line%5d: %r" % (lineNumber, row))
                if len(row) >= 1:
                    rowId = str(row[0]).lower() 
                    if rowId == InterfaceControlDocument._ID_CHECK:
                        self.addCheck(row[1:])
                    elif rowId == InterfaceControlDocument._ID_DATA_FORMAT:
                        self.addDataFormat(row[1:])
                    elif rowId == InterfaceControlDocument._ID_FIELD_RULE:
                        self.addFieldFormat(row[1:])
                    elif rowId.strip():
                        raise IcdSyntaxError("first item in row %d is %r but must be empty or one of: %r" % (lineNumber, row[0], InterfaceControlDocument._VALID_IDS))
        finally:
            if needsOpen:
                icdFile.close()
        if self.dataFormat is None:
            raise IcdSyntaxError("ICD must contain a section describing the data format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_DATA_FORMAT)
        if not self.fieldFormats:
            raise IcdSyntaxError("ICD must contain a section describing at least one field format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_FIELD_RULE)
            
    def validate(self, dataFileToValidatePath):
        """
        Validate that all lines and items in dataFileToValidatePath conform to this interface.
        """
        assert self.dataFormat is not None
        assert dataFileToValidatePath is not None
        self._log.info("validate \"%s\"" % (dataFileToValidatePath))
        
        if self.dataFormat.getName() in [data.FORMAT_CSV, data.FORMAT_FIXED]:
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            if needsOpen:
                dataFile = open(dataFileToValidatePath, "rb")
            else:
                dataFile = dataFileToValidatePath
            dataReader = self.dataFormat.getEncoding().streamreader(dataFile)
        else:
            raise NotImplementedError("data format: %r" + self.dataFormat.getName())

        try:
            if self.dataFormat.getName() == data.FORMAT_CSV:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = self.dataFormat.getLineDelimiter()
                dialect.itemDelimiter = self.dataFormat.getItemDelimiter()
                # FIXME: Obtain quote char from ICD.
                dialect.quoteChar = "\""
                reader = parsers.parserReader(parsers.DelimitedParser(dataFile, dialect))
            elif self.dataFormat.getName() == data.FORMAT_FIXED:
                fieldLengths = []
                for fieldFormat in self.fieldFormats:
                    # Obtain the length of a fixed length item. We could easily do this in a
                    # single line and without assertions, but doing it the way seen below makes
                    # analyzing possible bugs a lot easier.
                    fieldLengthItems = fieldFormat.length.items
                    assert len(fieldLengthItems) == 1
                    firstLengthItem = fieldLengthItems[0]
                    assert len(firstLengthItem) == 2
                    fixedLength = firstLengthItem[0]
                    assert fixedLength == firstLengthItem[1]
                    longFixedLength = long(fixedLength)
                    fieldLengths.append(longFixedLength)
                reader = parsers.parserReader(parsers.FixedParser(dataFile, fieldLengths))
            else:
                raise NotImplementedError("data format: %r" + self.dataFormat.getName())
            # TODO: Replace rowNumber by position in parser.
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
                        except checks.CheckError, error:
                            raise checks.CheckError("row check failed: %r: %s" % (check.description, str(message)))
                    self._log.debug("accepted: %s" % row)
                    for listener in self.icdEventListeners:
                        listener.acceptedRow(row)
                except:
                    # Handle failed check and other errors.
                    # FIXME: Use handlers for "except fields.FieldValueError" and "except CutplaceError".
                    if isinstance(sys.exc_info()[1], (fields.FieldValueError)):
                        fieldName = self.fieldNames[itemIndex]
                        reason = "field %r does not match format: %s" % (fieldName, sys.exc_info()[1])
                    else:
                        reason = sys.exc_info()[1]
                    self._log.debug("rejected: %s" % row)
                    self._log.debug(reason, exc_info=self.logTrace)
                    for listener in self.icdEventListeners:
                        listener.rejectedRow(row, reason)
        finally:
            if needsOpen:
                dataFile.close()

        # Validate checks at end of data.
        for description, check in self.checkDescriptions.items():
            try:
                self._log.debug("checkAtEnd: %r" % (check))
                check.checkAtEnd()
            except checks.CheckError, message:
                reason = "check at end of data failed: %r: %s" % (check.description, message)
                self._log.error(reason)
                for listener in self.icdEventListeners:
                    listener.checkAtEndFailed(reason)
        
    def addIcdEventListener(self, listener):
        assert listener is not None
        assert listener not in self.icdEventListeners
        self.icdEventListeners.append(listener)
        
    def removeIcdEventListener(self, listener):
        assert listener is not None
        assert listener in self.icdEventListeners
        self.icdEventListeners.remove(listener)
