"""Check that can cover the whole data set."""
import fields

class CheckError(ValueError):
    """Error to be raised when a check fails."""
    pass

class AbstractCheck(object):
    """Abstract check to be used as base class for other checks. The constructor should be called by descendants,
     the other methods do nothing an can be left untouched."""
    def __init__(self, description, rule, fieldNames):
        assert description
        assert rule is not None
        assert fieldNames is not None
        self.description = description
        self.rule = rule
        self.fieldNames = fieldNames
    
    def checkRow(self, rowNumber, row):
        """"Check row and in case it is invalid raise CheckError. By default do nothing."""
        pass
    
    def checkAtEnd(self):
        """Check at at end of document when all rows have been read and in case something is wrong raise
        CheckError. By default do nothing."""
        pass
    
    def cleanup(self):
        """Clean up any resources allocated to perform the checks."""
        pass
        
class IsUniqueCheck(AbstractCheck):
    """Check to ensure that all rows are unique concerning certain key fields."""
    def __init__(self, description, rule, fieldNames):
        super(IsUniqueCheck, self).__init__(description, rule, fieldNames)
        self.fieldNamesToCheck = [fieldName.strip() for fieldName in rule.split(",")]
        if len(self.fieldNamesToCheck) == 0:
            raise fields.FieldLookupError("field names to compute unique value must be specified")
        self.fieldIndicesToCheck = []
        for fieldName in self.fieldNamesToCheck:
            try:
                fieldIndex = fieldNames.index(fieldName)
                self.fieldIndicesToCheck.append(fieldIndex)
            except LookupError:
                raise fields.FieldLookupError("field name %r must be replaced by one of: %s" % (fieldName, fieldNames))
        self.uniqueValues = {}
    
    def checkRow(self, rowNumber, row):
        key = []
        for fieldIndexToCheck in self.fieldIndicesToCheck:
            try:
                item = row[fieldIndexToCheck]
            except IndexError:
                item = None
            key.append(item)
        keyText = repr(key)
        if  keyText in self.uniqueValues:
            raise CheckError("unique %r has already occurred in row %d: %s" % (self.fieldNamesToCheck, self.uniqueValues[keyText], keyText))
        else:
            self.uniqueValues[keyText] = rowNumber
                                
