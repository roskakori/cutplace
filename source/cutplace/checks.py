"""Check that can cover the whole data set."""
import fields

class CheckError(ValueError):
    """Error to be raised when a check fails."""
    pass

class CheckSyntaxError(ValueError):
    """Error to be raised specification of check in ICD is broken."""
    
def _getFieldNameIndex(supposedFieldName, availableFieldNames):
    assert supposedFieldName is not None
    assert supposedFieldName == supposedFieldName.strip()
    assert availableFieldNames

    fieldName = supposedFieldName.strip()
    try:
        fieldIndex = availableFieldNames.index(fieldName)
    except LookupError:
        raise fields.FieldLookupError("field name %r must be replaced by one of: %r" % (fieldName, fieldNames))
    return fieldIndex
    
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
    
    def __str__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.description, self.rule, self.fieldNames)
        
class IsUniqueCheck(AbstractCheck):
    """Check to ensure that all rows are unique concerning certain key fields."""
    def __init__(self, description, rule, fieldNames):
        super(IsUniqueCheck, self).__init__(description, rule, fieldNames)
        self.fieldNamesToCheck = [fieldName.strip() for fieldName in rule.split(",")]
        if len(self.fieldNamesToCheck) == 0:
            raise fields.FieldLookupError("field names to compute unique value must be specified")
        self.uniqueValues = {}
    
    def checkRow(self, rowNumber, rowMap):
        key = []
        for fieldName in self.fieldNamesToCheck:
            item = rowMap[fieldName]
            key.append(item)
        keyText = repr(key)
        if  keyText in self.uniqueValues:
            raise CheckError("unique %r has already occurred in row %d: %s" % (self.fieldNamesToCheck, self.uniqueValues[keyText], keyText))
        else:
            self.uniqueValues[keyText] = rowNumber
                                