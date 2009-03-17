"""Standard field formats supported by cutplace."""
import logging
import re
import sys
import  time

_ELLIPSIS = "..."

def parsedRange(text):
    """Assume text is of the form "lower...upper" or "[value]" and return (lower, upper) respectively (value, value).
    In case text is empty, return None."""
    assert text is not None
    # TODO: Tokenize text properly.
    actualText = text.replace(" ", "")
    if actualText:
        eclipseIndex = actualText.find(_ELLIPSIS)
        if eclipseIndex < 0:
            lower = actualText
            upper = lower
        else:
            lower = actualText[:eclipseIndex]
            upper = actualText[eclipseIndex + len(_ELLIPSIS):]
        result = (lower, upper)
    else:
        result = None
    return result

def _longOrNone(fieldName, valueName, value):
    assert fieldName
    assert valueName
    assert value is not None

    if value.strip():
        try:
            result = long(value)
        except TypeError:
            raise ValueError("%s for %s must be an integer value but is: %s" % (valueName, fieldName, value))
    else:
        result = None
    return value

def parsedLongRange(name, text):
    """Assume text is of the form "lower...upper" or "[value]" and return (lower, upper) respectively (value, value),
    where lower, upper or value are long numbers."""
    assert name
    result = parsedRange(text)
    if result:
        lower = _longOrNone(name, "lower limit", result[0])
        upper = _longOrNone(name, "upper limit", result[1])
        if (lower is not None) and (upper is not None) and (lower > upper):
            raise ValueError("lower limit for %s is %d but must be at most %d" % (name, lower, upper))
        result = (lower, upper)
    return result

class FieldValueError(ValueError):
    """Error raised when AbstractFieldFormat.validate detects an error."""

class AbstractFieldFormat(object):
    """Format description of a field in a data file to validate."""
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        assert fieldName is not None
        assert fieldName, "fieldName must not be empty"
        assert isAllowedToBeEmpty is not None
        assert length is None or len(length) == 2, "len(%s) must be 2 but is %d" % (repr(length), len(length))
        assert rule is not None, "no rule must be expressed as \"\" instead of None" 

        self.fieldName = fieldName
        self.isAllowedToBeEmpty = isAllowedToBeEmpty
        self.length = length
        self.rule = rule
    
    def validateEmpty(self, value):
        if not self.isAllowedToBeEmpty:
            if not value:
                raise FieldValueError("value must not be empty")
    
    def validateLength(self, value):
        # Do we have some data at all?
        if not (self.isAllowedToBeEmpty and value == ""):
            # Do we have a length limit?
            if self.length is not None:
                # Actually validate length limit.
                valueLength = len(value)
                lowerLengthLimit = self.length[0]
                upperLengthLimit = self.length[1]
                if (lowerLengthLimit is not None) and (valueLength < long(lowerLengthLimit)):
                    raise FieldValueError("item must have at least %d characters but has %d: %s" % (long(lowerLengthLimit), valueLength, str(value)))
                if (upperLengthLimit is not None) and (valueLength > long(upperLengthLimit)):
                    raise FieldValueError("item must have at most %d characters but has %d: %s" % (long(upperLengthLimit), valueLength, str(value)))
         
    def validate(self, value):
        """Validate that value complies with field description. If not, raise FieldValueError."""
        raise NotImplementedError

class ChoiceFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(ChoiceFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
        self.choices = []
        for choice in rule.lower().split(","):
            self.choices.append(choice.strip())
        if not self.choices:
            raise ValueError("at least one choice must be specified for a %s field" % (repr("choice")))
    
    def validate(self, value):
        if value.lower() not in self.choices:
            raise FieldValueError("value is %s but must be one of: %s" % (repr(value), str(self.choices)))
    
class IntegerFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(IntegerFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
        # Default limit is 32 bit range. Python's integer scales to any range as long there is
        # enough memory available to represent it. If the user wants a bigger range, he has to
        # specify it.
        self.lower = - 2 ** 31
        self.upper = 2 ** 31 - 1
        (lower, upper) = parsedRange(rule)
        # FIXME: Add error message is lower or upper is not a long value.
        # FIXME: Add error message if lower >= upper.
        if lower:
            self.lower = long(lower)
        if upper:
            self.upper = long(upper)
   
    def validate(self, value):
        try:
            longValue = long(value)
        except ValueError:
            raise FieldValueError("value must be an integer number: %s" % (repr(value)))
        if longValue < self.lower:
            raise FieldValueError("value must at least %d but is %d" % (self.lower, longValue))
        if longValue > self.upper:
            raise FieldValueError("value must at most %d but is %d" % (self.upper, longValue))

class DateTimeFieldFormat(AbstractFieldFormat):
    # We can't use a dictionary here because checks for patterns need to be in order. In
    # particular, YYYY needs to be checked before YY.
    # FIXME: Add "%:%%" to escape percent sign.
    _humanReadableToStrptimeMap = ["DD:%d", "MM:%m", "YYYY:%Y", "YY:%y", "hh:%H", "mm:%M", "ss:%S"]
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(DateTimeFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
        self.humanReadableFormat = rule
        # Create an actual copy of the string.
        strptimeFormat = "".join(rule)
        for patternKeyValue in DateTimeFieldFormat._humanReadableToStrptimeMap:
            (key, value) = patternKeyValue.split(":")
            strptimeFormat = strptimeFormat.replace(key, value)
        self.strptimeFormat = strptimeFormat
   
    def validate(self, value):
        try:
            time.strptime(value, self.strptimeFormat)
        except ValueError:
            raise FieldValueError("date must match format %s (%s) but is: %s (%s)" % (self.humanReadableFormat, self.strptimeFormat, value, sys.exc_value))
                
class RegExFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(RegExFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
        self.regex = re.compile(rule, re.IGNORECASE | re.MULTILINE)
        self.rule = rule

    def validate(self, value):
        if not self.regex.match(value):
            raise FieldValueError("value %s must match regular expression: %s" % (repr(value), repr(self.rule)))

class PatternFieldFormat(AbstractFieldFormat):        
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(PatternFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
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
        
    def validate(self, value):
        if not self.regex.match(value):
            raise FieldValueError("value %s must match pattern: %s (regex %s)" % (repr(value), repr(self.rule), repr(self.pattern)))
            
class TextFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule):
        super(TextFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule)
   
    def validate(self, value):
        # TODO: Validate Text with rules like: 32..., a...z and so on.
        pass
