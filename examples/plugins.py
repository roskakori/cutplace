"""
Example plugins for cutplace.
"""

from cutplace import checks, errors, fields, ranges


class ColorFieldFormat(fields.AbstractFieldFormat):
    """
    Field format representing colors as their names.
    """

    def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
        super().__init__(
            field_name,
            is_allowed_to_be_empty,
            length,
            rule,
            data_format,
            # Use black as "empty" color.
            empty_value=(0.0, 0.0, 0.0),
        )

    def validated_value(self, color_name):
        assert color_name
        if color_name == "red":
            result = (1.0, 0.0, 0.0)
        elif color_name == "green":
            result = (0.0, 1.0, 0.0)
        elif color_name == "blue":
            result = (0.0, 1.0, 0.0)
        else:
            raise errors.FieldValueError("color name is %r but must be one of: red, green, blue" % color_name)
        return result


class FullNameLengthIsInRangeCheck(checks.AbstractCheck):
    """
    Check that total length of customer name is within the specified range.
    """

    def __init__(self, description, rule, available_field_names, location=None):
        super().__init__(description, rule, available_field_names, location)
        self._full_name_range = ranges.Range(rule)
        self.reset()

    def check_row(self, field_name_to_value_map, location):
        full_name = field_name_to_value_map["last_name"] + ", " + field_name_to_value_map["first_name"]
        full_name_length = len(full_name)
        self._full_name_range.validate("length of full name", full_name_length, location)
