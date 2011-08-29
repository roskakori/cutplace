"""
Standard field formats supported by cutplace.
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
import decimal
import keyword
import re
import sys
import time
import token

import data
import ranges
import tools
import _tools

# Expected suffix for classes that describe filed formats.
_FieldFormatClassSuffix = "FieldFormat"


class FieldValueError(tools.CutplaceError):
    """
    Error raised when `AbstractFieldFormat.validated` detects an error.
    """


class FieldLookupError(tools.CutplaceError):
    """
    Error raised when a field cannot be found.
    """


class FieldSyntaxError(tools.CutplaceError):
    """
    Error raised when a field definition in the ICD is broken.
    """


class AbstractFieldFormat(object):
    """
    Abstract format description of a field in a data file to validate which acts as base for all
    other field formats. To implement another field format, it is usually sufficient to:

      1. Overload `__init__()` but call ``super(..., self).__init__(...)`` from it.
      2. Implement `validatedValue()`.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, lengthText, rule, dataFormat, emptyValue=None):
        assert fieldName is not None
        assert fieldName, u"fieldName must not be empty"
        assert isAllowedToBeEmpty is not None
        assert rule is not None, u"to specify \"no rule\" use \"\" instead of None"
        assert dataFormat is not None

        self._fieldName = fieldName
        self._isAllowedToBeEmpty = isAllowedToBeEmpty
        self._length = ranges.Range(lengthText)
        self._rule = rule
        self._dataFormat = dataFormat
        self._emptyValue = emptyValue

    @property
    def fieldName(self):
        """The name of the field."""
        return self._fieldName

    @property
    def isAllowedToBeEmpty(self):
        """
        ``True`` if the field can be empty in the data set, resulting in `validated()` to return
        `emptyValue`.
        """
        return self._isAllowedToBeEmpty

    @property
    def length(self):
        """
        A `ranges.Range` describing the possible length of the value.
        """
        return self._length

    @property
    def rule(self):
        """
        A field format dependent rule to describe possible values.
        """
        return self._rule

    @property
    def dataFormat(self):
        """
        The `data.AbstractDataFormat` the data set has in case the field needs any properties from
        it to validate its value, for instance `data.KEY_DECIMAL_SEPARATOR`.
        """
        return self._dataFormat

    @property
    def emptyValue(self):
        """
        The result of `validated(value)` in case ``value`` is an empty string.
        """
        return self._emptyValue

    def validateCharacters(self, value):
        validCharacterRange = self.dataFormat.get(data.KEY_ALLOWED_CHARACTERS)
        if validCharacterRange is not None:
            for character in value:
                try:
                    validCharacterRange.validate("character", ord(character))
                except ranges.RangeValueError, error:
                    raise FieldValueError(u"value for fields %r must contain only valid characters: %s"
                                                 % (self.fieldName, error))

    def validateEmpty(self, value):
        if not self.isAllowedToBeEmpty:
            if not value:
                raise FieldValueError(u"value must not be empty")

    def validateLength(self, value):
        # Do we have some data at all?
        if self.length is not None and not (self.isAllowedToBeEmpty and value == ""):
            try:
                self.length.validate("length of '%s' with value %r" % (self.fieldName, value), len(value))
            except ranges.RangeValueError, error:
                raise FieldValueError(unicode(error))

    def validatedValue(self, value):
        """
        The `value` in its native type for this field.

        By the time this is called it is already ensured that:

          - `value` is not an empty string
          - `value` contains only valid characters
          - trailing blanks have been removed from `value` for fixed format data

        Concrete fields formats must override this because the default
        implementation just raises a `NotImplementedError`.
        """
        assert value

        raise NotImplementedError()

    def validated(self, value):
        """
        Validate that value complies with field description and return the value in its "native"
        type. If not, raise FieldValueError.
        """
        self.validateCharacters(value)
        if self.dataFormat.name == data.FORMAT_FIXED:
            result = self.dataFormat.strippedOfBlanks(value)
            self.validateEmpty(result)
            # Note: No need to validate the length with fixed length items.
        else:
            result = value
            self.validateEmpty(result)
            self.validateLength(result)
        if result:
            result = self.validatedValue(result)
        else:
            result = self.emptyValue
        return result

    def asIcdRow(self):
        """
        The description of the field format as row that can be written to an ICD except for the
        leading row mark "f".
        """
        if self.isAllowedToBeEmpty:
            isAllowedToBeEmptyMark = "X"
        else:
            isAllowedToBeEmptyMark = ""
        if self.length.items:
            lengthText = str(self._length)
        else:
            lengthText = ""
        fieldTypeName = self.__class__.__name__
        assert fieldTypeName.endswith(_FieldFormatClassSuffix), u"fieldTypeName=%r" % fieldTypeName
        fieldTypeName = fieldTypeName[:len(fieldTypeName) - len(_FieldFormatClassSuffix)]
        result = [
            self._fieldName,
            "",  # No example.
            isAllowedToBeEmptyMark,
            lengthText,
            fieldTypeName,
            self._rule,
        ]
        return result

    def __str__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.fieldName, self.isAllowedToBeEmpty, self.length, self.rule)


class ChoiceFieldFormat(AbstractFieldFormat):
    """
    Field format accepting only values from a pool of choices.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(ChoiceFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
        self.choices = []

        # Split rule into tokens, ignoring white space.
        tokens = _tools.tokenizeWithoutSpace(rule)

        # Extract choices from rule tokens.
        previousToky = None
        toky = tokens.next()
        while not _tools.isEofToken(toky):
            if _tools.isCommaToken(toky):
                # Handle comma after comma without choice.
                if previousToky:
                    previousTokyText = previousToky[1]
                else:
                    previousTokyText = None
                raise FieldSyntaxError(u"choice value must precede a comma (,) but found: %r" % previousTokyText)
            choice = _tools.tokenText(toky)
            if not choice:
                raise FieldSyntaxError(u"choice field must be allowed to be empty instead of containing an empty choice")
            self.choices.append(choice)
            toky = tokens.next()
            if not _tools.isEofToken(toky):
                if not _tools.isCommaToken(toky):
                    raise FieldSyntaxError(u"comma (,) must follow choice value %r but found: %r" % (choice, toky[1]))
                # Process next choice after comma.
                toky = tokens.next()
                if _tools.isEofToken(toky):
                    raise FieldSyntaxError(u"trailing comma (,) must be removed")
        if not self.isAllowedToBeEmpty and not self.choices:
            raise FieldSyntaxError(u"choice field without any choices must be allowed to be empty")

    def validatedValue(self, value):
        assert value

        if value not in self.choices:
            raise FieldValueError(u"value is %r but must be one of: %s"
                                   % (value, _tools.humanReadableList(self.choices)))
        return value


class DecimalFieldFormat(AbstractFieldFormat):
    """
    Field format accepting decimal numeric values, taking the data format properties
    `data.KEY_DECIMAL_SEPARATOR` and `data.KEY_THOUSANDS_SEPARATOR` into account.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue=None):
        super(DecimalFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue)
        if rule.strip():
            raise FieldSyntaxError(u"decimal rule must be empty")
        self.decimalSeparator = dataFormat.get(data.KEY_DECIMAL_SEPARATOR)
        self.thousandsSeparator = dataFormat.get(data.KEY_THOUSANDS_SEPARATOR)

        # TODO: In module data, check for same decimal/thousandsSeparator.
        assert self.decimalSeparator != self.thousandsSeparator

    def validatedValue(self, value):
        assert value

        translatedValue = ""
        foundDecimalSeparator = False
        for valueIndex in range(len(value)):
            characterToProcess = value[valueIndex]
            if characterToProcess == self.decimalSeparator:
                if foundDecimalSeparator:
                    raise FieldValueError(u"decimal field must contain only one decimal separator (%r): %r" % (self.decimalSeparator, value))
                translatedValue += "."
                foundDecimalSeparator = True
            elif self.thousandsSeparator and (characterToProcess == self.thousandsSeparator):
                if foundDecimalSeparator:
                    raise FieldValueError(u"decimal field must contain thousands separator (%r) only before decimal separator (%r): %r (position %d)"
                        % (self.thousandsSeparator, self.decimalSeparator, value, valueIndex + 1))
            else:
                translatedValue += characterToProcess
        try:
            result = decimal.Decimal(translatedValue)
        except Exception, error:
            message = u"value is %r but must be a decimal number: %s" % (value, error)
            raise FieldValueError(message)

        return result


class IntegerFieldFormat(AbstractFieldFormat):
    """
    Field format accepting numeric integer values with fractional part.
    """
    _DEFAULT_RANGE = "%d:%d" % (-2 ** 31, 2 ** 31 - 1)

    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue=None):
        super(IntegerFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue)
        # The default range is 32 bit. If the user wants a bigger range, he has to specify it.
        # Python's long scales to any range as long there is enough memory available to represent
        # it.
        self.rangeRule = ranges.Range(rule, IntegerFieldFormat._DEFAULT_RANGE)

    def validatedValue(self, value):
        assert value

        try:
            longValue = long(value)
        except ValueError:
            raise FieldValueError(u"value must be an integer number: %r" % value)
        try:
            self.rangeRule.validate("value", longValue)
        except ranges.RangeValueError, error:
            raise FieldValueError(unicode(error))
        return longValue


class DateTimeFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that represent dates or times.
    """
    # We can't use a dictionary here because checks for patterns need to be in order. In
    # particular, "%" need to be checked first, and "YYYY" needs to be checked before "YY".
    _humanReadableToStrptimeMap = ["%:%%", "DD:%d", "MM:%m", "YYYY:%Y", "YY:%y", "hh:%H", "mm:%M", "ss:%S"]

    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue=None):
        super(DateTimeFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue)
        self.humanReadableFormat = rule
        # Create an actual copy of the rule string so `replace()` will not modify the original..
        strptimeFormat = "".join(rule)

        for patternKeyValue in DateTimeFieldFormat._humanReadableToStrptimeMap:
            (key, value) = patternKeyValue.split(":")
            strptimeFormat = strptimeFormat.replace(key, value)
        self.strptimeFormat = strptimeFormat

    def validatedValue(self, value):
        assert value

        try:
            result = time.strptime(value, self.strptimeFormat)
        except ValueError:
            raise FieldValueError(u"date must match format %s (%s) but is: %r (%s)" % (self.humanReadableFormat, self.strptimeFormat, value, sys.exc_info()[1]))
        return result


class RegExFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a specified regular expression.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(RegExFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)

    def validatedValue(self, value):
        assert value

        if not self.regex.match(value):
            raise FieldValueError(u"value %r must match regular expression: %r" % (value, self.rule))
        return value


class PatternFieldFormat(AbstractFieldFormat):
    """
    Field format accepting values that match a pattern using "*" and "?" as place holders.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue=""):
        super(PatternFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue)
        # TODO: Use fnmatch. Ticket #37.
        pattern = ""
        for character in rule:
            if character == "?":
                pattern += "."
            elif character == "*":
                pattern += ".*"
            else:
                pattern += re.escape(character)
        self.regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.pattern = pattern

    def validatedValue(self, value):
        assert value

        if not self.regex.match(value):
            raise FieldValueError(u"value %r must match pattern: %r (regex %r)" % (value, self.rule, self.pattern))
        return value


class TextFieldFormat(AbstractFieldFormat):
    """
    Field format accepting any text.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue=""):
        super(TextFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue)

    def validatedValue(self, value):
        assert value
        # TODO: Validate Text with rules like: 32..., a...z and so on.
        return value


def getFieldNameIndex(supposedFieldName, availableFieldNames):
    """
    The index of `supposedFieldName` in `availableFieldNames`.

    In case it is missing, raise a `FieldLookupError`.
    """
    assert supposedFieldName is not None
    assert supposedFieldName == supposedFieldName.strip()
    assert availableFieldNames

    fieldName = supposedFieldName.strip()
    try:
        fieldIndex = availableFieldNames.index(fieldName)
    except ValueError:
        raise FieldLookupError(u"unknown field name %r must be replaced by one of: %s"
                                      % (fieldName, _tools.humanReadableList(availableFieldNames)))
    return fieldIndex


def validatedFieldName(supposedFieldName, location=None):
    """
    Same as ``supposedFieldName`` except with surrounding white space removed, provided that it
    describes a valid field name. Otherwise, raise a `FieldSyntaxError` pointing to ``location``.
    """
    tokens = _tools.tokenizeWithoutSpace(supposedFieldName)
    tokenType, result, _, _, _ = tokens.next()
    if tokenType != token.NAME:
        message = u"field name must be a valid Python name consisting of ASCII letters, underscore (%r) and digits but is: %r" % ("_", result)
        raise FieldSyntaxError(message, location)
    if keyword.iskeyword(result):
        raise FieldSyntaxError(u"field name must not be a Python keyword but is: %r" % result, location)
    toky = tokens.next()
    if not _tools.isEofToken(toky):
        raise FieldSyntaxError(u"field name must be a single word but is: %r" % supposedFieldName, location)
    return result
