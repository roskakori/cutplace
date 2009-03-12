"""Standard field formats supported by cutplace."""
import logging
import re

_ECLIPSE = "..."
def _parsedRange(text):
    """Assume text is of the form "[lower]...[upper]" and return (lower, upper)."""
    assert text is not None
    actualText = text.replace(" ", "")
    if actualText:
        eclipseIndex = actualText.find(_ECLIPSE)
        if eclipseIndex < 0:
            raise ValueError("range must be of format \"[lower]...[upper]\" but is: %s" % (repr(text)))
        lower = actualText[:eclipseIndex]
        upper = actualText[eclipseIndex + len(_ECLIPSE):]
        result = (lower, upper)
    else:
        result = ("", "")
    return result

class FieldValueError(ValueError):
    """Error raised when AbstractFieldFormat.validate detects an error."""

class AbstractFieldFormat(object):
    """Format description of a field in a data file to validate."""
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
            self.choices.append(choice.strip())
        if not self.choices:
            raise ValueError("at least one choice must be specified for a %s field" % (repr("choice")))
    
    def validate(self, value):
        if value.lower() not in self.choices:
            raise FieldValueError("value is %s but must be one of: %s" % (repr(value), str(self.choices)))
    
class IntegerFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        # Default limit is 32 bit range. Python's integer scales to any range as long there is
        # enough memory available to represent it. If the user wants a bigger range, he has to
        # specify it.
        self.lower = - 2 ** 31
        self.upper = 2 ** 31 - 1
        (lower, upper) = _parsedRange(rule)
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
        self.rule = rule

    def validate(self, value):
        if not self.regex.match(value):
            raise FieldValueError("value %s must match regular expression: %s" % (repr(value), repr(self.rule)))

class TextFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
   
    def validate(self, value):
        # TODO: Validate Text
        pass
