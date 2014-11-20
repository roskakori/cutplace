"""
Standard checks that can cover a whole row or data set.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
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
import io
import tokenize

from cutplace import fields
from cutplace import errors
from cutplace import _tools


class AbstractCheck(object):
    """
    Abstract check to be used as base class for other checks. The constructor should be called by
    descendants, the other methods do nothing and can be left untouched.
    """
    def __init__(self, description, rule, available_field_names, location_of_definition=None):
        """
        Create a check with the human readable ``description``, a ``rule`` in a check dependent
        syntax which can act on the fields listed in ``availableFieldNames`` (in the same order as
        defined in the ICD) and the optional ``locationOfDefinition`` in the ICD. If no
        ``locationOfDefinition`` is provided, `tools.createCallerInputLocation(["checks"])` is
        used.
        """
        assert description
        assert rule is not None
        assert available_field_names is not None

        if not available_field_names:
            raise errors.FieldLookupError("field names must be specified", location_of_definition)
        self._description = description
        self._rule = rule
        self._fieldNames = available_field_names
        if location_of_definition is None:
            self._location = errors.create_caller_input_location(["checks"])
        else:
            self._location = location_of_definition

    def reset(self):
        """
        Reset all internal resources needed by the check to keep track of the check conditions.
        By default do nothing.

        It is recommended that the `__init__()` of any child classes calls this method.

        This is called by `interface.InterfaceControlDocument.validate()` when starting to
        validate the data.
        """
        pass

    def check_row(self, row_map, location):
        """
        Check row and in case it is invalid raise `CheckError`. By default do nothing.

        ``RowMap`` is maps all field names to their respective value for this row, ``location`` is
        the `tools.InputLocation` where the row started in the input.
        """
        pass

    def check_at_end(self, location):
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
    def field_names(self):
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
    def __init__(self, description, rule, available_field_names, location=None):
        super(IsUniqueCheck, self).__init__(description, rule, available_field_names, location)

        self.fieldNamesToCheck = []

        # Extract field names to check from rule.
        rule_read_line = io.StringIO(rule).readline
        toky = tokenize.generate_tokens(rule_read_line)
        after_comma = True
        next_token = next(toky)
        unique_field_names = set()
        while not _tools.isEofToken(next_token):
            token_type = next_token[0]
            token_value = next_token[1]
            if after_comma:
                if token_type != tokenize.NAME:
                    raise errors.CheckSyntaxError("field name must contain only ASCII letters, numbers and underscores (_) "
                                                  + "but found: %r [token type=%r]" % (token_value, token_type))
                try:
                    fields.getFieldNameIndex(token_value, available_field_names)
                    if token_value in unique_field_names:
                        raise errors.CheckSyntaxError("duplicate field name for unique check must be removed: %s" % token_value)
                    unique_field_names.add(token_value)
                except errors.FieldLookupError as error:
                    raise errors.CheckSyntaxError(str(error))
                self.fieldNamesToCheck.append(token_value)
            elif not _tools.isCommaToken(next_token):
                raise errors.CheckSyntaxError("after field name a comma (,) must follow but found: %r" % token_value)
            after_comma = not after_comma
            next_token = next(toky)
        if not len(self.fieldNamesToCheck):
            raise errors.CheckSyntaxError("rule must contain at least one field name to check for uniqueness")
        self.reset()

    def reset(self):
        self.unique_values = {}

    def check_row(self, row_map, location):
        key = []
        for fieldName in self.fieldNamesToCheck:
            item = row_map[fieldName]
            key.append(item)
        key_text = repr(key)
        see_also_location = self.unique_values.get(key_text)
        if see_also_location is not None:
            raise errors.CheckError("unique %r has already occurred: %s" % (self.fieldNamesToCheck, key_text),
                                    location, see_also_message="location of previous occurrence",
                                    see_also_location=see_also_location)
        else:
            self.unique_values[key_text] = copy.copy(location)


class DistinctCountCheck(AbstractCheck):
    """
    Check to ensure that the number of different values in a field matches an expression.
    """
    _COUNT_NAME = "count"

    def __init__(self, description, rule, available_field_names, location=None):
        super(DistinctCountCheck, self).__init__(description, rule, available_field_names, location)
        rule_read_line = io.StringIO(rule).readline
        tokens = tokenize.generate_tokens(rule_read_line)
        first_token = next(tokens)

        # Obtain and validate field to count.
        if first_token[0] != tokenize.NAME:
            raise errors.CheckSyntaxError("rule must start with a field name but found: %r" % first_token[1])
        self.fieldNameToCount = first_token[1]
        fields.getFieldNameIndex(self.fieldNameToCount, available_field_names)
        line_where_field_name_ends, column_where_field_name_ends = first_token[3]
        assert column_where_field_name_ends > 0
        assert line_where_field_name_ends == 1

        # Build and test Python expression for validation.
        self.expression = DistinctCountCheck._COUNT_NAME + rule[column_where_field_name_ends:]
        self.reset()
        self._eval()

    def reset(self):
        self.distinct_values_to_count_map = {}

    def _distinct_count(self):
        return len(self.distinct_values_to_count_map)

    def _eval(self):
        local_variables = {DistinctCountCheck._COUNT_NAME: self._distinct_count()}
        try:
            result = eval(self.expression, {}, local_variables)
        except Exception as message:
            raise errors.CheckSyntaxError("cannot evaluate count expression %r: %s" % (self.expression, message))
        if result not in [True, False]:
            raise errors.CheckSyntaxError("count expression %r must result in %r or %r, but test resulted in: %r" %
                                          (self.expression, True, False, result))
        return result

    def check_row(self, row_map, location):
        value = row_map[self.fieldNameToCount]
        try:
            self.distinct_values_to_count_map[value] += 1
        except KeyError:
            self.distinct_values_to_count_map[value] = 1

    def check_at_end(self, location):
        if not self._eval():
            raise errors.CheckError("distinct count is %d but check requires: %r" %
                                    (self._distinct_count(), self.expression), location)
