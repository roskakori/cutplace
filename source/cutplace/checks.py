"""
Standard checks that can cover a whole row or data set.
"""
import fields
import StringIO
import tokenize
import tools

class CheckError(tools.CutplaceError):
    """
    Error to be raised when a check fails.
    """

class CheckSyntaxError(tools.CutplaceError):
    """
    Error to be raised when the specification of check in the ICD is broken.
    """
    
def _getFieldNameIndex(supposedFieldName, availableFieldNames):
    """
    The index of `supposedFieldName` in `availableFieldNames`.
    
    In case it is missing, raise a `fields.FieldLookupError`.
    """
    assert supposedFieldName is not None
    assert supposedFieldName == supposedFieldName.strip()
    assert availableFieldNames

    fieldName = supposedFieldName.strip()
    try:
        fieldIndex = availableFieldNames.index(fieldName)
    except ValueError:
        raise fields.FieldLookupError("field name %r must be replaced by one of: %r" % (fieldName, availableFieldNames))
    return fieldIndex
    
class AbstractCheck(object):
    """
    Abstract check to be used as base class for other checks. The constructor should be called by
    descendants, the other methods do nothing and can be left untouched.
    """
    def __init__(self, description, rule, fieldNames):
        assert description
        assert rule is not None
        assert fieldNames is not None
        self.description = description
        self.rule = rule
        self.fieldNames = fieldNames
    
    def checkRow(self, rowNumber, row):
        """"
        Check row and in case it is invalid raise CheckError. By default do nothing.
        """
        pass
    
    def checkAtEnd(self):
        """
        Check at at end of document when all rows have been read and in case something is wrong
        raise CheckError. By default do nothing.
        """
        pass
    
    def cleanup(self):
        """Clean up any resources allocated to perform the checks."""
        pass
    
    def __str__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.description, self.rule, self.fieldNames)
        
class IsUniqueCheck(AbstractCheck):
    """
    Check to ensure that all rows are unique concerning certain key fields.
    """
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

class DistinctCountCheck(AbstractCheck):
    """
    Check to ensure that the number of different values in a field matches an expression.
    """
    _COUNT_NAME = "count"
    
    def __init__(self, description, rule, availableFieldNames):
        super(DistinctCountCheck, self).__init__(description, rule, availableFieldNames)
        ruleReadLine = StringIO.StringIO(rule).readline
        tokens = tokenize.generate_tokens(ruleReadLine)
        firstToken = tokens.next()
        
        # Obtain and validate field to count.
        if firstToken[0] != tokenize.NAME:
            raise CheckSyntaxError("rule must start with a field name but found: %r" % firstToken[1])
        self.fieldNameToCount = firstToken[1]
        _getFieldNameIndex(self.fieldNameToCount, availableFieldNames)
        lineWhereFieldNameEnds, columnWhereFieldNameEnds = firstToken[3]
        assert columnWhereFieldNameEnds > 0
        assert lineWhereFieldNameEnds == 1

        # Build and test Python expression for validation.
        self.expression = DistinctCountCheck._COUNT_NAME + rule[columnWhereFieldNameEnds:]
        self.distinctValuesToCountMap = {}
        self._eval()

    def _distinctCount(self):
        return len(self.distinctValuesToCountMap)
    
    def _eval(self):
        localVariables = {DistinctCountCheck._COUNT_NAME:self._distinctCount()}
        try:
            result = eval(self.expression, {}, localVariables)
        except Exception, message:
            raise CheckSyntaxError("cannot evaluate count expression %r: %s" % (self.expression, message))
        if result not in [True, False]:
            raise CheckSyntaxError("count expression %r must result in true or false, but test resulted in: %r" % (self.expression, result))
        return result
        
    def checkRow(self, rowNumber, rowMap):
        value = rowMap[self.fieldNameToCount]
        try:
            self.distinctValuesToCountMap[value] += 1
        except KeyError:
            self.distinctValuesToCountMap[value] = 1

    def checkAtEnd(self):
        if not self._eval():
            raise CheckError("distinct count is %d but check requires: %r" % (self._distinctCount(), self.expression))
