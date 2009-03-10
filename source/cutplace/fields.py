"""Standard field formats supported by cutplace."""
import logging
import re

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
            self.choices.append(choice.trim())
        if not choices:
            raise ValueError("at least one choice must be specified for a %s field" % (repr("choice")))
    
    def validate(self, value):
        if value.lower() not in sefl.choices:
            raise FieldValueError("value is %s but must be one of: %s" % (repr(value), str(choices)))
    
class IntegerFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
        self.regex = re.compile(rule)
   
    def validate(self, value):
        try:
            longValue = long(value)
        except ValueError:
            raise FieldValueError("value must be an integer number: %s" % (repr(value)))
        if self.rule:
            # TODO: Validate range
            pass 

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

    def validate(self, value):
        if not self.regex.match(value):
            raise FieldValueError("value %s must match regular expression: %s" % (repr(value), repr(self.rule)))

class TextFieldFormat(AbstractFieldFormat):
    def __init__(self, fieldName, rule, isAllowedToBeEmpty):
        super(AbstractFieldFormat, self).__init__(rule, isAllowedToBeEmpty)
   
    def validate(self, value):
        # TODO: Validate Text
        pass
