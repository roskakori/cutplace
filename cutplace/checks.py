"""
Standard checks that can cover a whole row or data set.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
import tokenize

from cutplace import _tools, errors, fields
from cutplace._tools import generated_tokens


class AbstractCheck(object):
    """
    Abstract check to be used as base class for other checks. The constructor should be called by
    descendants, the other methods do nothing and can be left untouched.
    """

    def __init__(self, description, rule, available_field_names, location_of_definition=None):
        r"""
        Create a check.

        :param str description: human readable description of the check
        :param str rule: the check conditions to validate
        :param list available_field_names: the names of the fields available for the check (typically referring \
            to :py:attr:`cutplace.interface.Cid.field_names`)
        :param location_of_definition: location in the CID where the check was declared to be (used by error \
            messages); if ``None``, use ``cutplace.errors.create_caller_location(['checks'])``
        :type location_of_definition: :py:class:`~cutplace.errors.Location` or None
        """
        assert description
        assert rule is not None
        assert available_field_names is not None

        if not available_field_names:
            raise errors.InterfaceError("field names must be specified before check", location_of_definition)
        self._description = description
        self._rule = rule
        self._field_names = available_field_names
        if location_of_definition is None:
            self._location = errors.create_caller_location(["checks"])
            self._location_of_rule = self._location
        else:
            self._location = copy.copy(location_of_definition)
            self._location.set_cell(1)
            self._location_of_rule = copy.copy(location_of_definition)
            self._location_of_rule.set_cell(3)

    def reset(self):
        """
        Reset all internal resources needed by the check to keep track of the check conditions.
        By default do nothing.

        It is recommended that the :py:meth:`.__init__` of any child class calls this method.

        This is called by :py:meth:`cutplace.validio.Reader.validate_rows` when starting to validate the data.
        """
        pass

    def check_row(self, field_name_to_value_map, location):
        r"""
        Check row and in case it is invalid raise :py:exc:`errors.CheckError`. By default do
        nothing.

        :param str field_name_to_value_map: map of all field names to their respective value for the current row
        :param cutplace.errors.Location location: location where the row started in the input.
        :raises cutplace.errors.CheckError: if the ``row`` does not conform
        """
        pass

    def check_at_end(self, location):
        """
        Check global conditions at at end of document when all rows have been read. By default do nothing.

        :param errors.Location location: location of the last row in the input
        :raises cutplace.errors.CheckError: if the input does not conform
        """
        pass

    def cleanup(self):
        """
        Clean up any resources allocated to perform the checks. By default, so nothing.
        """
        pass

    def __str__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.description, self.rule)

    @property
    def description(self):
        """
        A human readable description of the check as specified in the CID, for example
        ``'id must be unique'``.

        :rtype: str
        """
        return self._description

    @property
    def rule(self):
        """
        A rule as specified in the CID describing the check conditions; its syntax depends on the actual
        check.

        :rtype: str
        """
        return self._rule

    @property
    def location(self):
        """
        Location in the CID or source code where the check was defined.

        :rtype: errors.Location
        """
        return self._location

    @property
    def location_of_rule(self):
        """
        The location of the rule column in the CID. This is particular useful when raising a
        :py:exc:`errors.InterfaceError` for a broken rule during :py:meth:`__init__`.

        :rtype: errors.Location
        """
        return self._location

    @property
    def field_names(self):
        """
        Names of fields declared in the CID using this field format. They can be used by checks
        that need to extract field values by name or that have a `rule` referring to certain
        fields.

        The order of field names in this list matches the order of declaration in the CID.
        """
        return self._field_names


class IsUniqueCheck(AbstractCheck):
    """
    Check to ensure that all rows are unique concerning certain key fields.
    """

    def __init__(self, description, rule, available_field_names, location=None):
        super().__init__(description, rule, available_field_names, location)

        self._field_names_to_check = []
        self._row_key_to_location_map = None
        self.reset()

        # Extract field names to check from rule.
        toky = generated_tokens(rule)
        after_comma = True
        next_token = next(toky)
        unique_field_names = set()
        while not _tools.is_eof_token(next_token):
            token_type = next_token[0]
            token_value = next_token[1]
            if after_comma:
                if token_type != tokenize.NAME:
                    raise errors.InterfaceError(
                        "field name must contain only ASCII letters, numbers and underscores (_) "
                        + "but found: %r [token type=%r]" % (token_value, token_type),
                        self.location_of_rule,
                    )
                try:
                    fields.field_name_index(token_value, available_field_names, location)
                    if token_value in unique_field_names:
                        raise errors.InterfaceError(
                            "duplicate field name for unique check must be removed: %s" % token_value,
                            self.location_of_rule,
                        )
                    unique_field_names.add(token_value)
                except errors.InterfaceError as error:
                    raise errors.InterfaceError(str(error))
                self._field_names_to_check.append(token_value)
            elif not _tools.is_comma_token(next_token):
                raise errors.InterfaceError(
                    "after field name a comma (,) must follow but found: %r" % token_value, self.location_of_rule
                )
            after_comma = not after_comma
            next_token = next(toky)
        if not len(self._field_names_to_check):
            raise errors.InterfaceError(
                "rule must contain at least one field name to check for uniqueness", self.location_of_rule
            )

    def reset(self):
        self._row_key_to_location_map = {}

    def check_row(self, field_name_to_value_map, location):
        row_key = tuple(field_name_to_value_map[field_name] for field_name in self._field_names_to_check)
        see_also_location = self._row_key_to_location_map.get(row_key)
        if see_also_location is not None:
            raise errors.CheckError(
                "values for %r must be unique: %s" % (self._field_names_to_check, row_key),
                location,
                see_also_message="location of first occurrence",
                see_also_location=see_also_location,
            )
        else:
            self._row_key_to_location_map[row_key] = copy.copy(location)


class DistinctCountCheck(AbstractCheck):
    """
    Check to ensure that the number of different values in a field matches an expression.
    """

    _COUNT_NAME = "count"

    def __init__(self, description, rule, available_field_names, location=None):
        super().__init__(description, rule, available_field_names, location)

        tokens = generated_tokens(rule)
        first_token = next(tokens)

        # Obtain and validate field to count.
        if first_token[0] != tokenize.NAME:
            raise errors.InterfaceError(
                "rule must start with a field name but found: %r" % first_token[1], self.location_of_rule
            )
        self._field_name_to_count = first_token[1]
        fields.field_name_index(self._field_name_to_count, available_field_names, location)
        line_where_field_name_ends, column_where_field_name_ends = first_token[3]
        assert column_where_field_name_ends > 0
        assert line_where_field_name_ends == 1

        # Build and test Python expression for validation.
        self._expression = DistinctCountCheck._COUNT_NAME + rule[column_where_field_name_ends:]
        self._distinct_value_to_count_map = None
        self.reset()
        self._eval()

    def reset(self):
        self._distinct_value_to_count_map = {}

    def _distinct_count(self):
        return len(self._distinct_value_to_count_map)

    def _eval(self):
        """
        The current result of `self._expression`.
        """
        local_variables = {DistinctCountCheck._COUNT_NAME: self._distinct_count()}
        try:
            result = eval(self._expression, {}, local_variables)
        except Exception as message:
            raise errors.InterfaceError(
                "cannot evaluate count expression %r: %s" % (self._expression, message), self.location_of_rule
            )
        if result not in (True, False):
            raise errors.InterfaceError(
                "count expression %r must result in %r or %r, but test resulted in: %r"
                % (self._expression, True, False, result),
                self.location_of_rule,
            )
        return result

    def check_row(self, field_name_to_value_map, location):
        value = field_name_to_value_map[self._field_name_to_count]
        try:
            self._distinct_value_to_count_map[value] += 1
        except KeyError:
            self._distinct_value_to_count_map[value] = 1

    def check_at_end(self, location):
        if not self._eval():
            raise errors.CheckError(
                "distinct count is %d but check requires: %r" % (self._distinct_count(), self._expression), location
            )
