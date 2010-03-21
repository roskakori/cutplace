"""
Standard checks that can cover a whole row or data set.
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
        raise fields.FieldLookupError("unknown field name %r must be replaced by one of: %s"
                                      % (fieldName, tools.humanReadableList(availableFieldNames)))
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
    
    def reset(self):
        """
        Reset all internal resources needed by the check to keep track of the check conditions.
        By default do nothing.
        
        It is recommended that the `__init__()` of any child classes calls this method.
        
        This is called by `interface.InterfaceControlDocument.validate()` when starting to
        validate the data.
        """
        pass

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
        return "%s(%r, %r)" % (self.__class__.__name__, self.description, self.rule)
        
class IsUniqueCheck(AbstractCheck):
    """
    Check to ensure that all rows are unique concerning certain key fields.
    """
    def __init__(self, description, rule, availableFieldNames):
        super(IsUniqueCheck, self).__init__(description, rule, availableFieldNames)
        
        self.fieldNamesToCheck = []

        # Extract field names to check from rule.
        ruleReadLine = StringIO.StringIO(rule).readline
        toky = tokenize.generate_tokens(ruleReadLine)
        afterComma = True
        nextToken = toky.next()
        while not tools.isEofToken(nextToken):
            tokenType = nextToken[0]
            tokenValue = nextToken[1]
            if afterComma:
                # TODO: Report error when the same field name shows up again.
                if tokenType != tokenize.NAME:
                    raise CheckSyntaxError("field name must contain only ASCII letters, numbers and underscores (_) "
                                           + "but found: %r [token type=%r]" % (tokenValue, tokenType))
                try:
                    _getFieldNameIndex(tokenValue, availableFieldNames)
                except fields.FieldLookupError, error:
                    raise CheckSyntaxError(str(error))
                self.fieldNamesToCheck.append(tokenValue)
            elif not tools.isCommaToken(nextToken):
                raise CheckSyntaxError("after field name a comma (,) must follow but found: %r" % (tokenValue))
            afterComma = not afterComma
            nextToken = toky.next()
        if not len(self.fieldNamesToCheck):
            raise CheckSyntaxError("rule must contain at least one field name to check for uniqueness")
        self.reset()
            
    def reset(self):
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
        self.reset()
        self._eval()

    def reset(self):
        self.distinctValuesToCountMap = {}

    def _distinctCount(self):
        return len(self.distinctValuesToCountMap)
    
    def _eval(self):
        localVariables = {DistinctCountCheck._COUNT_NAME:self._distinctCount()}
        try:
            result = eval(self.expression, {}, localVariables)
        except Exception, message:
            raise CheckSyntaxError("cannot evaluate count expression %r: %s" % (self.expression, message))
        if result not in [True, False]:
            raise CheckSyntaxError("count expression %r must result in %r or %r, but test resulted in: %r" % (self.expression, True, False, result))
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
