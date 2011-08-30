"""
Standard checks that can cover a whole row or data set.
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
import copy
import StringIO
import tokenize

import fields
import tools
import _tools


class CheckError(tools.CutplaceError):
    """
    Error to be raised when a check fails.
    """


class CheckSyntaxError(tools.CutplaceError):
    """
    Error to be raised when the specification of check in the ICD is broken.
    """


class AbstractCheck(object):
    """
    Abstract check to be used as base class for other checks. The constructor should be called by
    descendants, the other methods do nothing and can be left untouched.
    """
    def __init__(self, description, rule, availableFieldNames, locationOfDefinition=None):
        """
        Create a check with the human readable ``description``, a ``rule`` in a check dependent
        syntax which can act on the fields listed in ``availableFieldNames`` (in the same order as
        defined in the ICD) and the optional ``locationOfDefinition`` in the ICD. If no
        ``locationOfDefinition`` is provided, `tools.createCallerInputLocation(["checks"])` is
        used.
        """
        assert description
        assert rule is not None
        assert availableFieldNames is not None

        if not availableFieldNames:
            raise fields.FieldLookupError(u"field names must be specified", locationOfDefinition)
        self._description = description
        self._rule = rule
        self._fieldNames = availableFieldNames
        if locationOfDefinition is None:
            self._location = tools.createCallerInputLocation(["checks"])
        else:
            self._location = locationOfDefinition

    def reset(self):
        """
        Reset all internal resources needed by the check to keep track of the check conditions.
        By default do nothing.

        It is recommended that the `__init__()` of any child classes calls this method.

        This is called by `interface.InterfaceControlDocument.validate()` when starting to
        validate the data.
        """
        pass

    def checkRow(self, rowMap, location):
        """
        Check row and in case it is invalid raise `CheckError`. By default do nothing.

        ``RowMap`` is maps all field names to their respective value for this row, ``location`` is
        the `tools.InputLocation` where the row started in the input.
        """
        pass

    def checkAtEnd(self, location):
        """
        Check at at end of document when all rows have been read and in case something is wrong
        raise `CheckError`. By default do nothing.

        ``Location`` is the `tools.InputLocation` of the last row in the input.
        """
        pass

    def cleanup(self):
        """Clean up any resources allocated to perform the checks."""
        pass

    def __str__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.description, self.rule)

    @property
    def description(self):
        """
        A short description of the check as specified in the ICD, for example "id must be unique".
        """
        return self._description

    @property
    def rule(self):
        """
        A rule string describing what the check actually should do; its syntax depends on the actual
        check.
        """
        return self._rule

    @property
    def location(self):
        """
        The `tools.InputLocation` where the check was defined.
        """
        return self._location

    @property
    def fieldNames(self):
        """
        Names of fields declared in the ICD using this field format. They can be used by checks
        that need to extract field values by name or that have a `rule` referring to certain
        fields.

        The order of field names in this list match the order of declaration in the ICD.
        """
        return self._location


class IsUniqueCheck(AbstractCheck):
    """
    Check to ensure that all rows are unique concerning certain key fields.
    """
    def __init__(self, description, rule, availableFieldNames, location=None):
        super(IsUniqueCheck, self).__init__(description, rule, availableFieldNames, location)

        self.fieldNamesToCheck = []

        # Extract field names to check from rule.
        ruleReadLine = StringIO.StringIO(rule).readline
        toky = tokenize.generate_tokens(ruleReadLine)
        afterComma = True
        nextToken = toky.next()
        uniqueFieldNames = set()
        while not _tools.isEofToken(nextToken):
            tokenType = nextToken[0]
            tokenValue = nextToken[1]
            if afterComma:
                if tokenType != tokenize.NAME:
                    raise CheckSyntaxError(u"field name must contain only ASCII letters, numbers and underscores (_) "
                                           + "but found: %r [token type=%r]" % (tokenValue, tokenType))
                try:
                    fields.getFieldNameIndex(tokenValue, availableFieldNames)
                    if tokenValue in uniqueFieldNames:
                        raise CheckSyntaxError(u"duplicate field name for unique check must be removed: %s" % tokenValue)
                    uniqueFieldNames.add(tokenValue)
                except fields.FieldLookupError, error:
                    raise CheckSyntaxError(unicode(error))
                self.fieldNamesToCheck.append(tokenValue)
            elif not _tools.isCommaToken(nextToken):
                raise CheckSyntaxError(u"after field name a comma (,) must follow but found: %r" % (tokenValue))
            afterComma = not afterComma
            nextToken = toky.next()
        if not len(self.fieldNamesToCheck):
            raise CheckSyntaxError(u"rule must contain at least one field name to check for uniqueness")
        self.reset()

    def reset(self):
        self.uniqueValues = {}

    def checkRow(self, rowMap, location):
        key = []
        for fieldName in self.fieldNamesToCheck:
            item = rowMap[fieldName]
            key.append(item)
        keyText = repr(key)
        seeAlsoLocation = self.uniqueValues.get(keyText)
        if seeAlsoLocation is not None:
            raise CheckError(u"unique %r has already occurred: %s" % (self.fieldNamesToCheck, keyText),
                location, seeAlsoMessage="location of previous occurrence", seeAlsoLocation=seeAlsoLocation)
        else:
            self.uniqueValues[keyText] = copy.copy(location)


class DistinctCountCheck(AbstractCheck):
    """
    Check to ensure that the number of different values in a field matches an expression.
    """
    _COUNT_NAME = "count"

    def __init__(self, description, rule, availableFieldNames, location=None):
        super(DistinctCountCheck, self).__init__(description, rule, availableFieldNames, location)
        ruleReadLine = StringIO.StringIO(rule).readline
        tokens = tokenize.generate_tokens(ruleReadLine)
        firstToken = tokens.next()

        # Obtain and validate field to count.
        if firstToken[0] != tokenize.NAME:
            raise CheckSyntaxError(u"rule must start with a field name but found: %r" % firstToken[1])
        self.fieldNameToCount = firstToken[1]
        fields.getFieldNameIndex(self.fieldNameToCount, availableFieldNames)
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
        localVariables = {DistinctCountCheck._COUNT_NAME: self._distinctCount()}
        try:
            result = eval(self.expression, {}, localVariables)
        except Exception, message:
            raise CheckSyntaxError(u"cannot evaluate count expression %r: %s" % (self.expression, message))
        if result not in [True, False]:
            raise CheckSyntaxError(u"count expression %r must result in %r or %r, but test resulted in: %r" % (self.expression, True, False, result))
        return result

    def checkRow(self, rowMap, location):
        value = rowMap[self.fieldNameToCount]
        try:
            self.distinctValuesToCountMap[value] += 1
        except KeyError:
            self.distinctValuesToCountMap[value] = 1

    def checkAtEnd(self, location):
        if not self._eval():
            raise CheckError(u"distinct count is %d but check requires: %r" % (self._distinctCount(), self.expression), location)
