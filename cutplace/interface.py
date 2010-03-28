"""
Interface control document (ICD) describing all aspects of a data driven interface.
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

class ValidationEventListener(object):
    """
    Listener to process events during `InterfaceControlDocument.validate()`.
    
    To act on events, define a class inheriting from `ValidationEventListener` and overwrite the
    methods for those events you are interested in:

    >>> class MyValidationEventListener(ValidationEventListener):
    ...     def rejectedRow(self, row, error):
    ...         print "%r" % row
    ...         print "error: %s" % error
    ... 

    Create a new listener:
    
    >>> listener = MyValidationEventListener()
    
    To actually receive events, you have to attach it to an ICD:
    
    >>> icd = InterfaceControlDocument()
    >>> icd.addValidationEventListener(listener)
    >>> # Add data format and field formats and call `icd.validate()`

    When you are done, remove the listener so its resources are released:
    
    >>> icd.removeValidationEventListener(listener)
    """
    # TODO: Rename to `BaseValidationEventListener`.
    # FIXME: Add error positions: rowNumber, itemNumber, indexInItem
    def acceptedRow(self, row):
        pass
    
    def rejectedRow(self, row, error):
        pass
    
    def checkAtEndFailed(self, error):
        pass
    
    # TODO: Ponder: Would there be any point in `dataFormatFailed(self, error)`?

class IcdSyntaxError(tools.CutplaceError):
    """
    General syntax error in the specification of the ICD.
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
    # Header used by Excel (and other MS Office applications).
    _EXCEL_HEADER = "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    
    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.dataFormat = None
        self.fieldNames = []
        self.fieldFormats = []
        self.fieldNameToFormatMap = {}
        self.checkDescriptions = {}
        self.ValidationEventListeners = []
        # TODO: Add logTrace as property and let setter check for True or False.
        self.logTrace = False
        self._resetCounts()
        
    def _resetCounts(self):
        self.acceptedCount = 0
        self.rejectedCount = 0
        self.failedChecksAtEndCount = 0
        self.passedChecksAtEndCount = 0
    
    def _createClass(self, defaultModuleName, type, classNameAppendix, typeName):
        assert defaultModuleName
        assert type
        assert classNameAppendix
        assert typeName
        
        # FIXME: Remove check for "fields." and provide a proper test case in testFieldTypeWithModule
        # using a "real" module.
        if type.startswith("fields."):
            type = type[7:]
        lastDotIndex = type.rfind(".")
        if (lastDotIndex >= 0):
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
            raise fields.FieldSyntaxError("cannot find %s: %s" % (typeName, str(type)))
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
                    raise data.DataFormatSyntaxError("data format must be set only once, but has been set already to: %r" % self.dataFormat.name)
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
        1) optional: example value (can be empty)
        3) optional: empty flag ("X"=field is allowed to be empty)
        4) optional: length ("lower:upper")
        2) optional: field type
        5) optional: rule to validate field (depending on type)
        
        Further values in `items` are ignored.
        
        Any errors detected result in a `fields.FieldSyntaxError`.
        """
        assert items is not None

        if self.dataFormat is None:
            raise IcdSyntaxError("data format must be specified before first field")

        fieldName = None
        fieldExample = None
        fieldIsAllowedToBeEmpty = False
        fieldLength = None
        fieldType = None
        fieldRule = ""
        
        itemCount = len(items)
        if itemCount >= 1:
            # Obtain field name.
            try:
                fieldName = tools.validatedPythonName("field name", items[0])
            except NameError, error:
                raise fields.FieldSyntaxError(str(error))

            # Obtain example.
            if itemCount >= 2:
                fieldExample = items[1]
            else:
                fieldExample = ""

            # Obtain "empty" flag. 
            if itemCount >= 3:
                fieldIsAllowedToBeEmptyText = items[2].strip().lower()
                if fieldIsAllowedToBeEmptyText == InterfaceControlDocument._EMPTY_INDICATOR:
                    fieldIsAllowedToBeEmpty = True
                elif fieldIsAllowedToBeEmptyText:
                    raise fields.FieldSyntaxError("mark for empty field must be %r or empty but is %r" 
                                                  % (InterfaceControlDocument._EMPTY_INDICATOR,
                                                     fieldIsAllowedToBeEmptyText))

            # Obtain length.
            if itemCount >= 4:
                fieldLength = items[3].strip()

            # Obtain field type.
            if itemCount >= 5:
                fieldTypeItem = items[4].strip()
                if fieldTypeItem:
                    fieldType = ""
                    fieldTypeParts = fieldTypeItem.split(".")
                    try:
                        for part in fieldTypeParts:
                            if fieldType:
                                fieldType += "."
                            fieldType += tools.validatedPythonName("field type part", part)
                        assert fieldType, "empty field type must be detected by validatedPythonName()"
                    except NameError, error:
                        raise fields.FieldSyntaxError(str(error))

            # Obtain rule.
            if itemCount >= 6:
                fieldRule = items[5].strip()

            # Validate fixed fields.
            if isinstance(self.dataFormat, data.FixedDataFormat):
                if not fieldLength:
                    raise fields.FieldSyntaxError("field length must be specified with fixed data format")
                # FIXME: Validate that field length is fixed size.

            # Obtain class for field type.
            if not fieldType:
                fieldType = "Text"
            fieldClass = self._createFieldFormatClass(fieldType);
            self._log.debug("create field: %s(%r, %r, %r)" % (fieldClass.__name__, fieldName, fieldType, fieldRule))
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            fieldFormat.__init__(fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule, self.dataFormat)

            # Validate example in case there is one.
            if fieldExample:
                try:
                    fieldFormat.validated(fieldExample)
                except fields.FieldValueError, error:
                    raise IcdSyntaxError("cannot validate example for field %r: %s" % (fieldName, error))

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
            raise fields.FieldSyntaxError("field format row (marked with %r) must at least contain a field name" % InterfaceControlDocument._ID_FIELD_RULE)

        assert fieldName
        assert fieldExample is not None
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
                # TODO: Remember location where check was defined to later include it in error message.
                self.checkDescriptions[checkDescription] = check
            else:
                raise checks.CheckSyntaxError("check description must be used only once: %r" % (checkDescription)) 
        else:
            raise checks.CheckSyntaxError("check row (marked with %r) must contain at least 2 columns" % InterfaceControlDocument._ID_FIELD_RULE)

    def _fittingReader(self, icdReadable, encoding):
        """
        A reader fitting the contents of `icdReadable`.
        """
        assert icdReadable is not None
        assert encoding is not None
        
        result = None
        icdHeader = icdReadable.read(4)
        self._log.debug("icdHeader=%r" % icdHeader)
        if icdHeader == InterfaceControlDocument._ODS_HEADER:
            # Consider ICD to be ODS.
            icdReadable.seek(0)
            result = parsers.odsReader(icdReadable)
        else:
            icdHeader += icdReadable.read(4)
            icdReadable.seek(0)
            if icdHeader == InterfaceControlDocument._EXCEL_HEADER:
                # Consider ICD to be Excel.
                result = parsers.excelReader(icdReadable)
            else:
                # Consider ICD to be CSV.
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = parsers.AUTO
                dialect.itemDelimiter = parsers.AUTO
                dialect.quoteChar = "\""
                dialect.escapeChar = "\""
                result = parsers.delimitedReader(icdReadable, dialect, encoding)
        return result
    
    def read(self, icdFilePath, encoding="ascii"):
        """"
        Read the ICD as specified in `icdFilePath`.
        
        - `icdPath` - either the path of a file or a `StringIO`
        - `encoding` - the name of the encoding to use when reading the ICD; depending the the
        file type this might be ignored 
        """
        assert icdFilePath is not None
        assert encoding is not None

        needsOpen = isinstance(icdFilePath, types.StringTypes)
        if needsOpen:
            icdFile = open(icdFilePath, "rb")
        else:
            icdFile = icdFilePath
        try:
            reader = self._fittingReader(icdFile, encoding)
            rowNumber = 0
            for row in reader:
                rowNumber += 1
                self._log.debug("parse icd row%5d: %r" % (rowNumber, row))
                if len(row) >= 1:
                    rowId = str(row[0]).lower() 
                    if rowId == InterfaceControlDocument._ID_CHECK:
                        self.addCheck(row[1:])
                    elif rowId == InterfaceControlDocument._ID_DATA_FORMAT:
                        self.addDataFormat(row[1:])
                    elif rowId == InterfaceControlDocument._ID_FIELD_RULE:
                        self.addFieldFormat(row[1:])
                    elif rowId.strip():
                        raise IcdSyntaxError("first item in row %d is %r but must be empty or one of: %s"
                                             % (rowNumber, row[0],
                                                tools.humanReadableList(InterfaceControlDocument._VALID_IDS)))
        except tools.CutplaceUnicodeError, error:
            raise tools.CutplaceUnicodeError("ICD must conform to encoding %r: %s" % (encoding, error))
        finally:
            if needsOpen:
                icdFile.close()
        if self.dataFormat is None:
            raise IcdSyntaxError("ICD must contain a section describing the data format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_DATA_FORMAT)
        if not self.fieldFormats:
            raise IcdSyntaxError("ICD must contain a section describing at least one field format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_FIELD_RULE)
            
    def _obtainReadable(self, dataFileToValidatePath):
        """
        A tuple consisting of the following:
        
        1. A file like readable object for `dataFileToValidatePath`, which can be a string describing the
        path to a file, or a `StringIO` to data.
        2. A flag indicating whether the caller needs to call `close()` on the readable object once he is
        done reading it.
        """
        assert self.dataFormat is not None
        assert dataFileToValidatePath is not None

        if self.dataFormat.name in [data.FORMAT_CSV, data.FORMAT_EXCEL, data.FORMAT_ODS]:
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            if needsOpen:
                dataFile = open(dataFileToValidatePath, "rb")
            else:
                dataFile = dataFileToValidatePath
        elif self.dataFormat.name == data.FORMAT_FIXED:
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            if needsOpen:
                dataFile = codecs.open(dataFileToValidatePath, "rb", self.dataFormat.encoding)
            else:
                dataFile = dataFileToValidatePath
        else: # pragma: no cover
            raise NotImplementedError("data format: %r" % self.dataFormat.name)
        
        return (dataFile, needsOpen)
        
    def _reject_row(self, row, reason):
        assert reason
        self._log.debug("rejected: %s" % row)
        self._log.debug(reason, exc_info=self.logTrace)
        self.rejectedCount += 1
        for listener in self.ValidationEventListeners:
            listener.rejectedRow(row, reason)

    def validate(self, dataFileToValidatePath, validationListener=None):
        """
        Validate that all rows and items in `dataFileToValidatePath` conform to this interface.
        The optional `validationListener` is a  `ValidationEventListener` which is informed
        about detailed results of the validation. 
        """
        # FIXME: Split up `validate()` in several smaller methods.
        assert dataFileToValidatePath is not None
        
        self._log.info("validate \"%s\"" % (dataFileToValidatePath))
        self._resetCounts()
        for check in self.checkDescriptions.values():
            check.reset()

        (dataFile, needsOpen) = self._obtainReadable(dataFileToValidatePath)
        try:
            if self.dataFormat.name == data.FORMAT_CSV:
                dialect = parsers.DelimitedDialect()
                dialect.lineDelimiter = self.dataFormat.get(data.KEY_LINE_DELIMITER)
                dialect.itemDelimiter = self.dataFormat.get(data.KEY_ITEM_DELIMITER)
                dialect.quoteChar = self.dataFormat.get(data.KEY_QUOTE_CHARACTER)
                # FIXME: Set escape char according to ICD.
                reader = parsers.delimitedReader(dataFile, dialect, encoding=self.dataFormat.encoding)
            elif self.dataFormat.name == data.FORMAT_EXCEL:
                sheet = self.dataFormat.get(data.KEY_SHEET)
                reader = parsers.excelReader(dataFile, sheet)
            elif self.dataFormat.name == data.FORMAT_FIXED:
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
                reader = parsers.fixedReader(dataFile, fieldLengths)
            elif self.dataFormat.name == data.FORMAT_ODS:
                sheet = self.dataFormat.get(data.KEY_SHEET)
                reader = parsers.odsReader(dataFile, sheet)
            else: # pragma: no cover
                raise NotImplementedError("data format: %r" % self.dataFormat.name)
            # TODO: Replace rowNumber by position in parser.
            
            # Obtain various values from the data format that will be used to various checks.
            firstRowToValidateFieldsIn = self.dataFormat.get(data.KEY_HEADER)
            assert firstRowToValidateFieldsIn is not None
            assert firstRowToValidateFieldsIn >= 0

            # Validate data row by row.
            try:
                if validationListener is not None:
                    self.addValidationEventListener(validationListener)
                rowNumber = 0
                try:
                    for row in reader:
                        itemIndex = 0
                        rowNumber += 1
                        
                        if rowNumber > firstRowToValidateFieldsIn:
                            try:
                                # Validate all items of the current row and collect their values in `rowMap`.
                                maxItemCount = min(len(row), len(self.fieldFormats))
                                rowMap = {}
                                while itemIndex < maxItemCount:
                                    item = row[itemIndex]
                                    assert not isinstance(item, str), "item at row %d, column %d must be Unicode string instead of plain string: %r" % (rowNumber, itemIndex + 1, item)
                                    fieldFormat = self.fieldFormats[itemIndex]
                                    if __debug__ and self._log.isEnabledFor(logging.DEBUG):
                                        self._log.debug("validate item %d/%d: %r with %s <- %r" % (itemIndex + 1, len(self.fieldFormats), item, fieldFormat, row))  
                                    rowMap[fieldFormat.fieldName] = fieldFormat.validated(item) 
                                    itemIndex += 1
                                if itemIndex != len(row):
                                    itemIndex -= 1
                                    raise checks.CheckError("unexpected data must be removed after item %d" % (itemIndex))
                                elif len(row) < len(self.fieldFormats):
                                    missingFieldNames = self.fieldNames[(len(row) - 1):]
                                    raise checks.CheckError("row must contain items for the following fields: %r" % missingFieldNames)
            
                                # Validate row checks.
                                for description, check in self.checkDescriptions.items():
                                    try:
                                        if __debug__ and self._log.isEnabledFor(logging.DEBUG):
                                            self._log.debug("check row: %s" % check)  
                                        check.checkRow(rowNumber, rowMap)
                                    except checks.CheckError, error:
                                        raise checks.CheckError("row check failed: %r: %s" % (check.description, error))
                                self._log.debug("accepted: %s" % row)
                                self.acceptedCount += 1
                                for listener in self.ValidationEventListeners:
                                    listener.acceptedRow(row)
                            except data.DataFormatValueError:
                                raise
                            except tools.CutplaceError, error:
                                isFieldValueError = isinstance(error, fields.FieldValueError)
                                if isFieldValueError:
                                    fieldName = self.fieldNames[itemIndex]
                                    reason = "field %r must match format: %s" % (fieldName, error)
                                else:
                                    reason = str(error)
                                self._reject_row(row, reason)
                except tools.CutplaceUnicodeError, error:
                    self._reject_row([], error)
                    # raise data.DataFormatValueError("cannot read row %d: %s" % (rowNumber + 2, error))
            finally:
                if validationListener is not None:
                    self.removeValidationEventListener(validationListener)
        finally:
            if needsOpen:
                dataFile.close()

        # Validate checks at end of data.
        for description, check in self.checkDescriptions.items():
            try:
                self._log.debug("checkAtEnd: %s" % (check))
                check.checkAtEnd()
                self.passedChecksAtEndCount += 1
            except checks.CheckError, message:
                reason = "check at end of data failed: %r: %s" % (check.description, message)
                self._log.error(reason)
                self.failedChecksAtEndCount += 1
                for listener in self.ValidationEventListeners:
                    listener.checkAtEndFailed(reason)
        
    def addValidationEventListener(self, listener):
        assert listener is not None
        assert listener not in self.ValidationEventListeners
        self.ValidationEventListeners.append(listener)
        
    def removeValidationEventListener(self, listener):
        assert listener is not None
        assert listener in self.ValidationEventListeners
        self.ValidationEventListeners.remove(listener)
