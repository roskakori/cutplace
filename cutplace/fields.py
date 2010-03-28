"""
Standard field formats supported by cutplace.
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
import data
import decimal
import locale
import logging
import range
import re
import sys
import time
import tools

# TODO: Rename `validate`to `validated` to express that it is a function.

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
    Format description of a field in a data file to validate.
    """
    def __init__(self, fieldName, isAllowedToBeEmpty, lengthText, rule, dataFormat, emptyValue=None):
        assert fieldName is not None
        assert fieldName, "fieldName must not be empty"
        assert isAllowedToBeEmpty is not None
        assert rule is not None, "to specify \"no rule\" use \"\" instead of None" 
        assert dataFormat is not None

        self.fieldName = fieldName
        self.isAllowedToBeEmpty = isAllowedToBeEmpty
        self.length = range.Range(lengthText)
        self.rule = rule
        self.dataFormat = dataFormat
        self.emptyValue = emptyValue

    def validateCharacters(self, value):
        validCharacterRange = self.dataFormat.get(data.KEY_ALLOWED_CHARACTERS)
        if validCharacterRange is not None:
            for character in value:
                try:
                    validCharacterRange.validate("character", ord(character))
                except range.RangeValueError, error:
                    raise FieldValueError("value for fields %r must contain only valid characters: %s"
                                                 % (self.fieldName, error))
    
    def validateEmpty(self, value):
        if not self.isAllowedToBeEmpty:
            if not value:
                raise FieldValueError("value must not be empty")

    def validateLength(self, value):
        # Do we have some data at all?
        if self.length is not None and not (self.isAllowedToBeEmpty and value == ""):
            try:
                self.length.validate("length of '%s' with value %r" % (self.fieldName, value), len(value))
            except range.RangeValueError, error:
                raise FieldValueError(str(error))

    def validatedValue(self, value):
        """
        The `value` in its native type for this field.

        By the time this is called it is already ensured that:
        
        - `value` is not an empty string
        - `value` contains only valid characters
        - trailing blanks have been removed from `value`for fixed format data
        
        Concrete fields formats must override this because the default
        implementation just raises a `NotImplementedError`.
        """
        assert value
        
        raise NotImplementedError

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
    
    def __str__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.fieldName, self.isAllowedToBeEmpty, self.length, self.rule)
    
class ChoiceFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(ChoiceFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
        self.choices = []
        choiceIndex = 0
        # TODO: Parse choice  rule properly using tokenizer and accept strings too.
        for choice in rule.lower().split(","):
            choiceIndex += 1
            choice = choice.strip()
            if not choice:
                raise FieldSyntaxError("rule for a field of type %r must be a comma separated list of choices but choice #%d is empty"
                                       % ("choice", choiceIndex))
            self.choices.append(choice)
    
    def validatedValue(self, value):
        assert value

        if value.lower() not in self.choices:
            raise FieldValueError("value is %r but must be one of: %s"
                                   % (value, tools.humanReadableList(self.choices)))
        return value

class DecimalFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(DecimalFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat)
        if rule.strip():
            raise FieldSyntaxError("decimal rule must be empty")

    def validatedValue(self, value):
        assert value

        try:
            result = decimal.Decimal(value)
        except Exception, error:
            message = "value is %r but must be a decimal number: %s" % (value, error)
            raise FieldValueError(message)
        return result
        
class IntegerFieldFormat(AbstractFieldFormat):
    _DEFAULT_RANGE = "%d:%d" % (-2 ** 31, 2 ** 31 - 1)

    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(IntegerFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat)
        # The default range is 32 bit. If the user wants a bigger range, he has to specify it. 
        # Python's long scales to any range as long there is enough memory available to represent
        # it. 
        self.rangeRule = range.Range(rule, IntegerFieldFormat._DEFAULT_RANGE)
   
    def validatedValue(self, value):
        assert value
        
        try:
            longValue = long(value)
        except ValueError:
            raise FieldValueError("value must be an integer number: %r" % value)
        try:
            self.rangeRule.validate("value", longValue)
        except range.RangeValueError, error:
            raise FieldValueError(str(error))
        return longValue
    
class DateTimeFieldFormat(AbstractFieldFormat):
    # We can't use a dictionary here because checks for patterns need to be in order. In
    # particular, "%" need to be checked first, and "YYYY" needs to be checked before "YY".
    _humanReadableToStrptimeMap = ["%:%%", "DD:%d", "MM:%m", "YYYY:%Y", "YY:%y", "hh:%H", "mm:%M", "ss:%S"]

    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(DateTimeFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat)
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
            raise FieldValueError("date must match format %s (%s) but is: %r (%s)" % (self.humanReadableFormat, self.strptimeFormat, value, sys.exc_value))
        return result
                
class RegExFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(RegExFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)
        self.rule = rule

    def validatedValue(self, value):
        assert value
        
        if not self.regex.match(value):
            raise FieldValueError("value %r must match regular expression: %r" % (value, self.rule))
        return value

class PatternFieldFormat(AbstractFieldFormat):        
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(PatternFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
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
        self.rule = rule
        
    def validatedValue(self, value):
        assert value
        
        if not self.regex.match(value):
            raise FieldValueError("value %r must match pattern: %r (regex %r)" % (value, self.rule, self.pattern))
        return value
            
class TextFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(TextFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
   
    def validatedValue(self, value):
        assert value
        # TODO: Validate Text with rules like: 32..., a...z and so on.
        return value
