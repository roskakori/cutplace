"""
Interface control document (ICD) describing all aspects of a data driven interface.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import checks
import codecs
import keyword
import logging
import Queue
import sys
import threading
import token
import types

import data
import fields
import sniff
import tools
import _parsers
import _tools

_log = logging.getLogger("cutplace")

class BaseValidationListener(object):
    """
    Listener to process events during `InterfaceControlDocument.validate()`.

    To act on events, define a class inheriting from `BaseValidationListener` and overwrite the
    methods for the events you are interested in:

    >>> class MyValidationListener(BaseValidationListener):
    ...     def rejectedRow(self, row, error):
    ...         print "%r" % row
    ...         print "error: %s" % error
    ...

    Create a new listener:

    >>> listener = MyValidationListener()

    To actually receive events, you have to attach it to an ICD:

    >>> icd = InterfaceControlDocument()
    >>> icd.addValidationListener(listener)
    >>> # Add data format and field formats and call `icd.validate()`

    When you are done, remove the listener so its resources are released:

    >>> icd.removeValidationListener(listener)
    """
    def acceptedRow(self, row, location):
        """Called in case `row` at `tools.InputLocation` `location` has been accepted."""
        pass

    def rejectedRow(self, row, error):
        """
        Called in case ``row`` has been rejected due to ``error``, which is of type
        `tools.CutplaceError`. To learn the location in the input, query
        ``error.location``.
        """
        pass

    def checkAtEndFailed(self, error):
        """
        Called in case any of the checks performed at the end of processing
        the data due to `error`, which is of type `tools.CutplaceError`.
        """
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

    # Possible values for ``errors`` parameter of `validatedRows()`.
    _ERRORS_STRICT = "strict"
    _ERRORS_IGNORE = "ignore"
    _ERRORS_YIELD = "yield"
    _ALL_ERRORS_VALUES = [_ERRORS_STRICT, _ERRORS_IGNORE, _ERRORS_YIELD]

    def __init__(self):
        """
        Create an empty ICD. To set a data format and add fields and checks,
        use either `read` or `addDataFormat`, `addFieldFormat` and `addCheck`.
        """
        self._dataFormat = None
        self._fieldNames = []
        self._fieldFormats = []
        self._fieldNameToFormatMap = {}
        self._checkNames = []
        self._checkNameToCheckMap = {}
        self._validationListeners = []
        self._logTrace = False
        self._resetCounts()
        self._location = None

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
        _log.debug("create from %s class %s", str(moduleName), className)
        try:
            result = getattr(module, className)
        except AttributeError:
            raise fields.FieldSyntaxError("cannot find %s: %s" % (typeName, str(type)), self._location)
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
                if self._dataFormat is None:
                    self._dataFormat = data.createDataFormat(value)
                else:
                    raise data.DataFormatSyntaxError("data format must be set only once, but has been set already to: %r" % self._dataFormat.name, self._location)
            elif self._dataFormat is not None:
                self._dataFormat.set(key, value)
            else:
                raise data.DataFormatSyntaxError("first data format property name is %r but must be %r" % (key, data.KEY_FORMAT), self._location)
        else:
            raise data.DataFormatSyntaxError("data format line (marked with %r) must contain at least 2 columns" % InterfaceControlDocument._ID_DATA_FORMAT, self._location)

    def addFieldFormat(self, items):
        """
        Add field as described by `items`. The meanings of the items are:

        1) field name
        2) optional: example value (can be empty)
        3) optional: empty flag ("X"=field is allowed to be empty)
        4) optional: length ("lower:upper")
        5) optional: field type
        6) optional: rule to validate field (depending on type)

        Further values in `items` are ignored.

        Any errors detected result in a `fields.FieldSyntaxError`.
        """
        assert items is not None
        assert self._location is not None

        if self._dataFormat is None:
            raise IcdSyntaxError("data format must be specified before first field", self._location)

        fieldName = None
        fieldExample = None
        fieldIsAllowedToBeEmpty = False
        fieldLength = None
        fieldType = None
        fieldRule = ""

        itemCount = len(items)
        if itemCount >= 1:
            # Obtain field name.
            fieldNameText = items[0]
            tokens = _tools.tokenizeWithoutSpace(fieldNameText)
            tokenType, tokenText, _, _, _ = tokens.next()
            if tokenType != token.NAME:
                raise fields.FieldSyntaxError("field name must be a valid Python name consisting of ASCII letters, underscore (%r) and digits but is: %r" % ("_", tokenText),
                                              self._location)
            if keyword.iskeyword(tokenText):
                raise fields.FieldSyntaxError("field name must not be a Python keyword but is: %r" %  tokenText, self._location)
            fieldName = tokenText
            toky = tokens.next()
            if not _tools.isEofToken(toky):
                raise fields.FieldSyntaxError("field name must be a single word but is: %r" % fieldNameText, self._location)

            # Obtain example.
            if itemCount >= 2:
                self._location.advanceCell()
                fieldExample = items[1]
            else:
                fieldExample = ""

            # Obtain "empty" flag.
            if itemCount >= 3:
                self._location.advanceCell()
                fieldIsAllowedToBeEmptyText = items[2].strip().lower()
                if fieldIsAllowedToBeEmptyText == InterfaceControlDocument._EMPTY_INDICATOR:
                    fieldIsAllowedToBeEmpty = True
                elif fieldIsAllowedToBeEmptyText:
                    raise fields.FieldSyntaxError("mark for empty field must be %r or empty but is %r"
                                                  % (InterfaceControlDocument._EMPTY_INDICATOR,
                                                     fieldIsAllowedToBeEmptyText), self._location)

            # Obtain length.
            if itemCount >= 4:
                self._location.advanceCell()
                fieldLength = items[3].strip()

            # Obtain field type.
            if itemCount >= 5:
                self._location.advanceCell()
                fieldTypeItem = items[4].strip()
                if fieldTypeItem:
                    fieldType = ""
                    fieldTypeParts = fieldTypeItem.split(".")
                    try:
                        for part in fieldTypeParts:
                            if fieldType:
                                fieldType += "."
                            fieldType += _tools.validatedPythonName("field type part", part)
                        assert fieldType, "empty field type must be detected by validatedPythonName()"
                    except NameError, error:
                        raise fields.FieldSyntaxError(str(error), self._location)

            # Obtain rule.
            if itemCount >= 6:
                self._location.advanceCell()
                fieldRule = items[5].strip()

            # Obtain class for field type.
            if not fieldType:
                fieldType = "Text"
            fieldClass = self._createFieldFormatClass(fieldType);
            _log.debug("create field: %s(%r, %r, %r)", fieldClass.__name__, fieldName, fieldType, fieldRule)
            fieldFormat = fieldClass.__new__(fieldClass, fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule)
            fieldFormat.__init__(fieldName, fieldIsAllowedToBeEmpty, fieldLength, fieldRule, self._dataFormat)

            # Validate example in case there is one.
            if fieldExample:
                self._location.setCell(2)
                try:
                    fieldFormat.validated(fieldExample)
                except fields.FieldValueError, error:
                    raise IcdSyntaxError("cannot validate example for field %r: %s" % (fieldName, error), self._location)

            # Validate that field name is unique.
            if not self._fieldNameToFormatMap.has_key(fieldName):
                self._location.setCell(1)
                self._fieldNames.append(fieldName)
                self._fieldFormats.append(fieldFormat)
                # TODO: Remember location where field format was defined to later include it in error message
                self._fieldNameToFormatMap[fieldName] = fieldFormat
                _log.info("%s: defined field: %s", self._location, fieldFormat)
            else:
                raise fields.FieldSyntaxError("field name must be used for only one field: %s" % fieldName,
                                              self._location)

            # Validate field length for fixed format.
            if isinstance(self._dataFormat, data.FixedDataFormat):
                self._location.setCell(4)
                if fieldFormat.length.items:
                    fieldLengthIsBroken = True
                    if len(fieldFormat.length.items) == 1:
                        (lower, upper) = fieldFormat.length.items[0]
                        if lower == upper:
                            if lower < 1:
                                raise fields.FieldSyntaxError("length of field %r for fixed data format must be at least 1 but is : %s" % (fieldName, fieldFormat.length),
                                                              self._location)
                            fieldLengthIsBroken = False
                    if fieldLengthIsBroken:
                        raise fields.FieldSyntaxError("length of field %r for fixed data format must be a single value but is: %s" % (fieldName, fieldFormat.length),
                                                      self._location)
                else:
                    raise fields.FieldSyntaxError("length of field %r must be specified with fixed data format" % fieldName,
                                                  self._location)
        else:
            raise fields.FieldSyntaxError("field format row (marked with %r) must at least contain a field name" % InterfaceControlDocument._ID_FIELD_RULE,
                                          self._location)

        assert fieldName
        assert fieldExample is not None
        assert fieldType
        assert fieldRule is not None

    def addCheck(self, items):
        assert items is not None
        itemCount = len(items)
        if itemCount < 2:
            raise checks.CheckSyntaxError("check row (marked with %r) must contain at least 2 columns" % InterfaceControlDocument._ID_CHECK,
                                          self._location)
        checkDescription = items[0]
        checkType = items[1]
        if itemCount >= 3:
            checkRule = items[2]
        else:
            checkRule = ""
        _log.debug("create check: %s(%r, %r)", checkType, checkDescription, checkRule)
        checkClass = self._createCheckClass(checkType)
        check = checkClass.__new__(checkClass, checkDescription, checkRule, self._fieldNames, self._location)
        check.__init__(checkDescription, checkRule, self._fieldNames, self._location)
        self._location.setCell(1)
        existingCheck = self._checkNameToCheckMap.get(checkDescription)
        if existingCheck:
            raise checks.CheckSyntaxError("check description must be used only once: %r" % (checkDescription),
                                          self._location, "initial declaration", existingCheck.location)
        self._checkNameToCheckMap[checkDescription] = check
        self._checkNames.append(checkDescription)
        assert len(self.checkNames) == len(self._checkNameToCheckMap)

    def read(self, icdFilePath, encoding="ascii"):
        """
        Read the ICD as specified in ``icdFilePath``.

          - ``icdPath`` - either the path of a file or a ``StringIO``
          - ``encoding`` - the name of the encoding to use when reading the ICD; depending  on the
            file type this might be ignored
        """
        assert icdFilePath is not None
        assert encoding is not None

        needsOpen = isinstance(icdFilePath, types.StringTypes)
        if needsOpen:
            icdFile = open(icdFilePath, "rb")
        else:
            icdFile = icdFilePath
        self._location = tools.InputLocation(icdFilePath, hasCell=True)
        try:
            reader = sniff.createReader(icdFile, encoding=encoding)
            for row in reader:
                _log.debug("%s: parse %r", self._location, row)
                if len(row) >= 1:
                    rowId = str(row[0]).lower()
                    if rowId == InterfaceControlDocument._ID_CHECK:
                        # FIXME: Validate data format (required properties, contradictions)
                        self.addCheck(row[1:])
                    elif rowId == InterfaceControlDocument._ID_DATA_FORMAT:
                        # FIXME: Check that no fields or checks have been specified yet.
                        self.addDataFormat(row[1:])
                    elif rowId == InterfaceControlDocument._ID_FIELD_RULE:
                        # FIXME: Validate data format (required properties, contradictions)
                        self.addFieldFormat(row[1:])
                    elif rowId.strip():
                        raise IcdSyntaxError("first item in row is %r but must be empty or one of: %s"
                                             % (row[0], _tools.humanReadableList(InterfaceControlDocument._VALID_IDS)),
                                             self._location)
                self._location.advanceLine()
        except tools.CutplaceUnicodeError, error:
            raise tools.CutplaceUnicodeError("ICD must conform to encoding %r: %s" % (encoding, error))
        finally:
            if needsOpen:
                icdFile.close()
        if self._dataFormat is None:
            raise IcdSyntaxError("ICD must contain a section describing the data format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_DATA_FORMAT)
        if not self._fieldFormats:
            raise IcdSyntaxError("ICD must contain a section describing at least one field format (rows starting with %r)"
                                 % InterfaceControlDocument._ID_FIELD_RULE)
        # FIXME: In the end of read(), the following needs to be set: self._location = None

    def setLocationToSourceCode(self):
        """
        Set the location where the ICD is defined from to the caller location in the source code.
        This is necessary if you create the ICD manually calling `addDataFormat`, `addFieldFormat`
        etc. instead of using a file.
        """
        self._location = tools.createCallerInputLocation(hasCell=True);

    def _obtainReadable(self, dataFileToValidatePath):
        """
        A tuple consisting of the following:

          1. A file like readable object for `dataFileToValidatePath`, which can be a string describing the
             path to a file, or a ``StringIO`` to data.
          2. A `tools.InputLocation` pointing to the beginning of the first data item in the file.
          3. A flag indicating whether the caller needs to call ``close()`` on the readable object
             once it is done reading it.
        """
        assert self._dataFormat is not None
        assert dataFileToValidatePath is not None

        if self._dataFormat.name in (data.FORMAT_CSV, data.FORMAT_CSV, data.FORMAT_DELIMITED, data.FORMAT_EXCEL, data.FORMAT_ODS):
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            hasSheet = (self._dataFormat.name not in (data.FORMAT_CSV, data.FORMAT_DELIMITED))
            location = tools.InputLocation(dataFileToValidatePath, hasCell=True, hasSheet=hasSheet)
            if needsOpen:
                dataFile = open(dataFileToValidatePath, "rb")
            else:
                dataFile = dataFileToValidatePath
        elif self._dataFormat.name == data.FORMAT_FIXED:
            needsOpen = isinstance(dataFileToValidatePath, types.StringTypes)
            location = tools.InputLocation(dataFileToValidatePath, hasColumn=True, hasCell=True)
            if needsOpen:
                dataFile = codecs.open(dataFileToValidatePath, "rb", self._dataFormat.encoding)
            else:
                dataFile = dataFileToValidatePath
        else: # pragma: no cover
            raise NotImplementedError("data format: %r" % self._dataFormat.name)

        return (dataFile, location, needsOpen)

    def _rejectRow(self, row, reason, location):
        # TODO: Add "assert row is not None"?
        assert reason
        assert location
        isExceptionReason = isinstance(reason, Exception)
        isStringReason = isinstance(reason, types.StringTypes)
        assert isExceptionReason or isStringReason, "reason=%s:%r" % (type(reason), reason)
        assert isinstance(location, tools.InputLocation)
        _log.debug("rejected: %s", row)
        _log.debug(reason, exc_info=self.logTrace)
        self.rejectedCount += 1
        if isExceptionReason:
            error = reason
        else:
            error = tools.CutplaceError(reason, location)
        for listener in self._validationListeners:
            listener.rejectedRow(row, error)

    def _reader(self, dataFile):
        if self.dataFormat.name in (data.FORMAT_CSV, data.FORMAT_DELIMITED):
            dialect = _parsers.DelimitedDialect()
            dialect.lineDelimiter = self.dataFormat.get(data.KEY_LINE_DELIMITER)
            dialect.itemDelimiter = self.dataFormat.get(data.KEY_ITEM_DELIMITER)
            dialect.quoteChar = self.dataFormat.get(data.KEY_QUOTE_CHARACTER)
            # FIXME: Set escape char according to ICD.
            reader = _parsers.delimitedReader(dataFile, dialect, encoding=self.dataFormat.encoding)
        elif self.dataFormat.name == data.FORMAT_EXCEL:
            sheet = self.dataFormat.get(data.KEY_SHEET)
            reader = _parsers.excelReader(dataFile, sheet)
        elif self.dataFormat.name == data.FORMAT_FIXED:
            fieldLengths = []
            for fieldFormat in self._fieldFormats:
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
            reader = _parsers.fixedReader(dataFile, fieldLengths)
        elif self.dataFormat.name == data.FORMAT_ODS:
            sheet = self.dataFormat.get(data.KEY_SHEET)
            reader = _parsers.odsReader(dataFile, sheet)
        else: # pragma: no cover
            raise NotImplementedError("data format: %r" % self.dataFormat.name)
        return reader

    def validate(self, dataFileToValidatePath):
        """
        Validate that all rows and items in ``dataFileToValidatePath`` conform to this interface.
        If a validation listener has been attached using `addValidationListener`, it will be
        notified about any event occurring during validation.
        """
        # FIXME: Split up `validate()` in several smaller methods.
        assert dataFileToValidatePath is not None

        _log.info("validate \"%s\"", dataFileToValidatePath)
        self._resetCounts()
        for checkName in self.checkNames:
            check = self.getCheck(checkName)
            check.reset()

        (dataFile, location, needsOpen) = self._obtainReadable(dataFileToValidatePath)
        try:
            reader = self._reader(dataFile)
            # TODO: Replace rowNumber by position in parser.

            # Obtain values from the data format that will be used by various checks.
            firstRowToValidateFieldsIn = self._dataFormat.get(data.KEY_HEADER)
            assert firstRowToValidateFieldsIn is not None
            assert firstRowToValidateFieldsIn >= 0

            # Validate data row by row.
            # FIXME: Set location.sheet to actual sheet to validate
            try:
                for row in reader:
                    if location.line >= firstRowToValidateFieldsIn:
                        try:
                            # Validate all items of the current row and collect their values in `rowMap`.
                            maxItemCount = min(len(row), len(self._fieldFormats))
                            rowMap = {}
                            while location.cell < maxItemCount:
                                item = row[location.cell]
                                assert not isinstance(item, str), "%s: item must be Unicode string instead of plain string: %r" % (location, item)
                                fieldFormat = self._fieldFormats[location.cell]
                                if __debug__:
                                    _log.debug("validate item %d/%d: %r with %s <- %r", location.cell + 1, len(self._fieldFormats), item, fieldFormat, row)
                                rowMap[fieldFormat.fieldName] = fieldFormat.validated(item)
                                location.advanceCell()
                            if location.cell != len(row):
                                raise checks.CheckError("unexpected data must be removed after item %d" % (location.cell), location)
                            elif len(row) < len(self._fieldFormats):
                                missingFieldNames = self._fieldNames[(len(row) - 1):]
                                raise checks.CheckError("row must contain items for the following fields: %r" % missingFieldNames, location)

                            # Validate row checks.
                            for checkName in self.checkNames:
                                check = self.getCheck(checkName)
                                try:
                                    if __debug__:
                                        _log.debug("check row: ", check)
                                    check.checkRow(rowMap, location)
                                except checks.CheckError, error:
                                    raise checks.CheckError("row check failed: %r: %s" % (check.description, error), location)
                            _log.debug("accepted: %s", row)
                            self.acceptedCount += 1
                            for listener in self._validationListeners:
                                listener.acceptedRow(row, location)
                        except data.DataFormatValueError, error:
                            raise data.DataFormatValueError("cannot process data format", location, cause=error)
                        except tools.CutplaceError, error:
                            isFieldValueError = isinstance(error, fields.FieldValueError)
                            if isFieldValueError:
                                fieldName = self._fieldNames[location.cell]
                                reason = "field %r must match format: %s" % (fieldName, error)
                                error = fields.FieldValueError(reason, location)
                            self._rejectRow(row, error, location)
                    location.advanceLine()
            except tools.CutplaceUnicodeError, error:
                self._rejectRow([], error, location)
                # raise data.DataFormatValueError("cannot read row %d: %s" % (rowNumber + 2, error))
        finally:
            if needsOpen:
                dataFile.close()

        # Validate checks at end of data.
        # TODO: For checks at end, reset location to beginning of file and sheet
        for checkName in self.checkNames:
            check = self.getCheck(checkName)
            try:
                _log.debug("checkAtEnd: %s", check)
                check.checkAtEnd(location)
                self.passedChecksAtEndCount += 1
            except checks.CheckError, message:
                reason = "check at end of data failed: %r: %s" % (check.description, message)
                _log.error(reason)
                self.failedChecksAtEndCount += 1
                for listener in self._validationListeners:
                    listener.checkAtEndFailed(reason)

    def getFieldNameIndex(self, fieldName):
        """
        The column index of  the field named ``fieldName`` starting with 0.
        """
        # TODO: Use a dictionary to to change performance from O(n) to O(1).
        return fields.getFieldNameIndex(fieldName, self.fieldNames)

    def getFieldValueFor(self, fieldName, row):
        """
        The value for field ``fieldName`` in ``row``. This looks up the column of the field named
        ``fieldName`` and retrieves the data from the matching item in ``row``. If ``row`` does
        not contain the expected amount of field value, raise a `data.DataFormatValueError`.
        """
        assert fieldName is not None
        assert row is not None

        actualRowCount = len(row)
        expectedRowCount = len(self.fieldnames)
        if actualRowCount != expectedRowCount:
            location = tools.createCallerInputLocation()
            raise data.DataFormatValueError("row must have %d items but has %d: %s" % (expectedRowCount, actualRowCount, row), location)

        fieldIndex = self.getFieldNameIndex(fieldName)
        # The following condition must be ``true`` because any deviations should be been detected
        #  already by comparing expected and actual row count.
        assert fieldIndex < len(row)

        result = row[fieldIndex]
        return result

    @property
    def dataFormat(self):
        """
        The data format used by the this ICD; refer to the `data` module for possible formats.
        """
        return self._dataFormat

    @property
    def fieldNames(self):
        """List of field names defined in this ICD in the order they have been defined."""
        return self._fieldNames

    @property
    def checkNames(self):
        """List of check names in no particular order."""
        return self._checkNames

    def _getLogTrace(self):
        return self._logTrace

    def _setLogTrace(self, value):
        self._logTrace = value

    def getFieldFormat(self, fieldName):
        """
        The `fields.AbstractFieldFormat` for ``fieldName``. If no such field has been defined,
        raise a ``KeyError`` .
        """
        assert fieldName is not None
        return self._fieldNameToFormatMap[fieldName]

    def getCheck(self, checkName):
        """
        The `checks.AbstractCheck` for ``checkName``. If no such check has been defined,
        raise a ``KeyError`` .
        """
        assert checkName is not None
        return self._checkNameToCheckMap[checkName]

    def addValidationListener(self, listener):
        assert listener is not None
        assert listener not in self._validationListeners
        self._validationListeners.append(listener)

    def removeValidationListener(self, listener):
        assert listener is not None
        assert listener in self._validationListeners
        self._validationListeners.remove(listener)

    logTrace = property(_getLogTrace, _setLogTrace,
        doc="If ``True``, log stack trace on rejected data items or rows.")

def  validatedRows(icd, dataFileToValidatePath, errors="strict"):
    """
    Generator for rows described using ``icd`` in the data set found at ``dataFileToValidatePath``.
    This provides a convenient way to read and process data without having to implement an own
    reader.

    The ``errors`` parameter defines how to handle errors and takes the following values:

    * "strict" - raise an exception and stop processing data.
    * "ignore" - silently ignore errors and keep processing data.
    * "yield" - yield the error (inheriting from ``Exception``) instead of a row array; its up to
      the caller to check the return type before deciding how to process the result.
    """
    assert icd is not None
    assert dataFileToValidatePath is not None
    assert errors in InterfaceControlDocument._ALL_ERRORS_VALUES, \
        "errors=%r but must be one of: %s" % (errors, InterfaceControlDocument._ALL_ERRORS_VALUES)

    class ProducingValidationListener(BaseValidationListener):
        """
        Validation listener implementing a producer for rows or errors encountered while
        validating a data set.
        """
        def __init__(self, rowOrErrorQueue, errors):
            assert errors in InterfaceControlDocument._ALL_ERRORS_VALUES, \
                "errors=%r but must be one of: %s" % (errors, InterfaceControlDocument._ALL_ERRORS_VALUES)
            self._errors = errors
            self._rowOrErrorQueue = rowOrErrorQueue

        def produce(self, rowOrError):
            """
            Append ``rowOrError`` to producer queue with ``None`` indicating the end of the input.
            """
            self._rowOrErrorQueue.put(rowOrError)

        def acceptedRow(self, row, location):
            self.produce(row)

        def rejectedRow(self, row, error):
            self.produce(error)

        def checkAtEndFailed(self, error):
            self.produce(error)

    class ValidationThread(threading.Thread):
        """
        Thread to run a validation in order to produce rows and errors.
        """
        def __init__(self, icd, dataFileToValidatePath, rowOrErrorQueue, errors):
            assert icd is not None
            assert dataFileToValidatePath is not None
            assert rowOrErrorQueue is not None
            assert errors in InterfaceControlDocument._ALL_ERRORS_VALUES, \
                "errors=%r but must be one of: %s" % (errors, InterfaceControlDocument._ALL_ERRORS_VALUES)

            super(ValidationThread, self).__init__()
            self._icd = icd
            self._dataFileToValidatePath = dataFileToValidatePath
            self._rowOrErrorQueue = Queue.Queue(3)
            self._producingValidationListener = ProducingValidationListener(rowOrErrorQueue, errors)

        def run(self):
            self._icd.addValidationListener(self._producingValidationListener)
            try:
                self._icd.validate(self._dataFileToValidatePath)
                # Mark the end of the data set.
                self._producingValidationListener.produce(None)
            except Exception, error:
                self._producingValidationListener.produce(error)
            finally:
                self._icd.removeValidationListener(self._producingValidationListener)

    rowOrErrorQueue = Queue.Queue(3)
    validationThread = ValidationThread(icd, dataFileToValidatePath, rowOrErrorQueue, errors)
    validationThread.start()
    rowOrError = rowOrErrorQueue.get()
    while rowOrError is not None:
        isError = isinstance(rowOrError, Exception)
        if isError:
            if errors == InterfaceControlDocument._ERRORS_STRICT:
                # FIXME: Stop ``validationThread`` somehow to remove listener.
                raise rowOrError
            elif errors == InterfaceControlDocument._ERRORS_YIELD:
                yield rowOrError
            elif errors != InterfaceControlDocument._ERRORS_IGNORE:
                raise NotImplementedError("errors=%r"  % errors)
        else:
            assert isinstance(rowOrError, types.ListType), "rowOrError=%s: %r" % (type(rowOrError),rowOrError)
            yield rowOrError
        rowOrError = rowOrErrorQueue.get()
