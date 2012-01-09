"""
Example plugins for cutplace.
"""
from cutplace import checks
from cutplace import fields
from cutplace import ranges

class ColorFieldFormat(fields.AbstractFieldFormat):
    """Field format representing colors as their names."""
    def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
        super(ColorFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat,
                emptyValue=(0.0, 0.0, 0.0)) # Use black as "empty" color.

    def validatedValue(self, colorName):
        assert colorName
        if colorName == "red":
            result = (1.0, 0.0, 0.0)
        elif colorName == "green":
            result = (0.0, 1.0, 0.0)
        elif colorName == "blue":
            result = (0.0, 1.0, 0.0)
        else:
            raise fields.FieldValueError("color name is %r but must be one of: red, green, blue" % colorName)
        return result

class FullNameLengthIsInRangeCheck(checks.AbstractCheck):
    """Check that total length of customer name is within the specified range."""
    def __init__(self, description, rule, availableFieldNames, location=None):
        super(FullNameLengthIsInRangeCheck, self).__init__(description, rule, availableFieldNames, location)
        self._fullNameRange = ranges.Range(rule)
        self.reset()

    def checkRow(self, rowMap, location):
        fullName = rowMap["last_name"] + ", " + rowMap["first_name"]
        fullNameLength = len(fullName)
        try:
            self._fullNameRange.validate("full name", fullNameLength)
        except ranges.RangeValueError, error:
            raise CheckError("full name length is %d but must be in range %s: %r" \
                % (fullNameLength, self._fullNameRange, fullName))
