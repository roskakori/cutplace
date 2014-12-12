"""
Plugins to be used for tests.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from cutplace import fields


class CapitalizedTextFieldFormat(fields.AbstractFieldFormat):
    """
    Field format to validate for ``value`` to start in upper case. This is used to test plugin support.
    """
    def validated_value(self, value):
        if value:
            first_char = value[0]
            if not first_char.isupper():
                raise fields.FieldValueError("first character %r must be changed to upper case: %r"
                    % (first_char, value))
        return value
