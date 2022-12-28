"""
Ranges check if certain values are within it. This is used in several places of the CID, in
particular to specify the length limits for field values and the characters allowed for a data
format.
"""
import decimal

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
import token

from cutplace import _compat, _tools, errors

#: '...' as single character.
ELLIPSIS = "\u2026"

MAX_INTEGER = 2**31 - 1
MIN_INTEGER = -(2**31)

DEFAULT_INTEGER_RANGE_TEXT = "%d...%d" % (MIN_INTEGER, MAX_INTEGER)

#: Text to describe the upper limit of the default decimal range. 31 digits
#: are the maximum scale of IBM DB2 decimals, which seems to be the smallest
#: limit for currently practically relevant databases. Using 12 of these digits
#: for the precision is an arbitrary decision intended to cover most
#: practically relevant ranges.
MAX_DECIMAL_TEXT = "9999999999999999999.999999999999"
assert MAX_DECIMAL_TEXT.replace("9", "").replace(".", "") == ""
MIN_DECIMAL_TEXT = "-" + MAX_DECIMAL_TEXT
DEFAULT_DECIMAL_RANGE_TEXT = "%s...%s" % (MIN_DECIMAL_TEXT, MAX_DECIMAL_TEXT)

#: Precision (number of digits after the dot) to use for decimal numbers if
#: no range is specified.
DEFAULT_PRECISION = len(MAX_DECIMAL_TEXT.split(".")[1])

#: Scale (total number of digits) to use for decimal numbers if no range is
#: specified.
DEFAULT_SCALE = len(MAX_DECIMAL_TEXT) - 1


def code_for_number_token(name, value, location):
    """
    The numeric code for text representing an :py:class:`int` in ``value``.

    :param str name: the name of the value as it is known to the end user
    :param str value: the text that represents an :py:class:`int`
    :param cutplace.errors.Location location: the location of ``value`` or ``None``
    """
    assert name is not None
    assert value is not None

    try:
        # Note: base 0 automatically handles prefixes like 0x.
        result = int(value, 0)
    except ValueError:
        raise errors.InterfaceError(
            "numeric value for %s must be an integer number but is: %s" % (name, _compat.text_repr(value)), location
        )
    return result


def code_for_symbolic_token(name, value, location):
    """
    The numeric code for text representing an a symbolic name in ``value``,
    which has to be one of the values in
    :py:const:`cutplace.errors.NAME_TO_ASCII_CODE_MAP`.

    :param str name: the name of the value as it is known to the end user
    :param str value: the text that represents a symbolic name
    :param cutplace.errors.Location location: the location of ``value`` or ``None``
    """
    assert name is not None
    assert value is not None

    try:
        result = errors.NAME_TO_ASCII_CODE_MAP[value.lower()]
    except KeyError:
        valid_symbols = _tools.human_readable_list(sorted(errors.NAME_TO_ASCII_CODE_MAP.keys()))
        raise errors.InterfaceError(
            "symbolic name %s for %s must be one of: %s" % (_compat.text_repr(value), name, valid_symbols), location
        )
    return result


def code_for_string_token(name, value, location):
    """
    The numeric code for text representing an string with a single character in ``value``.

    :param str name: the name of the value as it is known to the end user
    :param str value: the text that represents a string with a single character
    :param cutplace.errors.Location location: the location of ``value`` or ``None``
    """
    assert name is not None
    assert value is not None
    assert len(value) >= 2
    left_quote = value[0]
    right_quote = value[-1]
    assert left_quote in "\"'", "left_quote=%r" % left_quote
    assert right_quote in "\"'", "right_quote=%r" % right_quote

    value_without_quotes = value[1:-1]
    if len(value_without_quotes) != 1:
        value_without_quotes = value_without_quotes.encode("utf-8").decode("unicode_escape")
        if len(value_without_quotes) != 1:
            raise errors.InterfaceError(
                "text for %s must be a single character but is: %s" % (name, _compat.text_repr(value)), location
            )
    return ord(value_without_quotes)


def create_range_from_length(length_range):
    """
    Create a range from length.
    """
    assert length_range is not None
    range_rule_text = ""
    if length_range.items is not None:
        if any((i[0] is not None and i[0] < 0) or (i[1] is not None and i[1] < 1) for i in length_range.items):
            raise errors.RangeValueError(
                "length must be a positive range and upper limit has to be greater than one, but is: %s"
                % length_range.description
            )

        for item in length_range.items:
            lower_length = item[0]
            upper_length = item[1]

            if lower_length is None or lower_length == 0 or lower_length == 1:
                if upper_length is None:
                    range_rule_text += ", "
                elif upper_length == 1:
                    range_rule_text += "0...9, "
                else:
                    range_rule_text += ("-" + ("9" * (upper_length - 1)) + "..." + ("9" * upper_length)) + ", "
            else:
                if upper_length is None:
                    range_rule_text += (
                        "...-1" + ("0" * (lower_length - 2)) + ", 1" + ("0" * (lower_length - 1)) + "..., "
                    )
                else:
                    range_rule_text += (
                        ("-" + ("9" * (upper_length - 1)) + "...-1" + ("0" * (lower_length - 2)))
                        + ", 1"
                        + (("0" * (lower_length - 1)) + "..." + ("9" * upper_length))
                        + ", "
                    )

        range_rule_text = range_rule_text.rstrip(" ,")
    else:
        range_rule_text = ""
    return Range(range_rule_text)


def _decimal_as_text(decimal_value, precision=DEFAULT_PRECISION):
    """
    Decimal value formatted as text always using a ``#.###`` format because
    ``str()`` might use scientific notation with values smaller than 1e-8.
    """
    assert isinstance(decimal_value, decimal.Decimal)
    assert precision >= 0

    return "%.*f" % (precision, decimal_value)


class Range(object):
    """
    A range that can be used to validate that a value is within it.
    """

    def __init__(self, description, default=None):
        """
        Setup a range as specified by ``description``.

        :param str description: a range description of the form \
          ``lower...upper`` or ``limit``. In case it is empty (``''``), any \
          value will be accepted by \
          :py:meth:`~cutplace.ranges.Range.validate()`. For example, \
          ``1...40`` accepts values between 1 and 40.
        :param str default: an alternative to use in case ``description`` is \
          ``None`` or empty.
        """
        assert default is None or (default.strip() != ""), "default=%r" % default

        # Find out if a `description` has been specified and if not, use optional `default` instead.
        has_description = (description is not None) and (description.strip() != "")
        if not has_description and default is not None:
            description = default
            has_description = True

        if not has_description:
            # Use empty ranges.
            self._description = None
            self._items = None
            self._lower_limit = None
            self._upper_limit = None
        else:
            self._description = description.replace("...", ELLIPSIS)
            self._items = []

            name_for_code = "range"
            location = None  # TODO: Add location where range is declared.
            tokens = _tools.tokenize_without_space(self._description)
            end_reached = False
            while not end_reached:
                lower = None
                upper = None
                ellipsis_found = False
                after_hyphen = False
                next_token = next(tokens)
                while not _tools.is_eof_token(next_token) and not _tools.is_comma_token(next_token):
                    next_type = next_token[0]
                    next_value = next_token[1]
                    if next_type in (token.NAME, token.NUMBER, token.STRING):
                        if next_type == token.NAME:
                            # Symbolic names, e.g. ``tab``.
                            value_as_int = code_for_symbolic_token(name_for_code, next_value, location)
                        elif next_type == token.NUMBER:
                            # Numbers, e.g. ``123``.
                            value_as_int = code_for_number_token(name_for_code, next_value, location)
                            if after_hyphen:
                                value_as_int *= -1
                                after_hyphen = False
                        elif next_type == token.STRING:
                            # Python strings, e.g. ``'abc'`` or ``"""abc"""``.
                            value_as_int = code_for_string_token(name_for_code, next_value, location)
                        elif (len(next_value) == 1) and not _tools.is_eof_token(next_token):
                            # Other single characters, e.g. ``,``; this is particular useful with delimiter properties.
                            value_as_int = ord(next_value)
                        else:
                            raise errors.InterfaceError(
                                "value for %s must a number, a single character or a symbolic name but is: %s"
                                % (name_for_code, _compat.text_repr(next_value)),
                                location,
                            )
                        if ellipsis_found:
                            if upper is None:
                                upper = value_as_int
                            else:
                                raise errors.InterfaceError(
                                    "range must have at most lower and upper limit but found another number: %s"
                                    % _compat.text_repr(next_value),
                                    location,
                                )
                        elif lower is None:
                            lower = value_as_int
                        else:
                            raise errors.InterfaceError(
                                "number must be followed by ellipsis (...) but found: %s"
                                % _compat.text_repr(next_value),
                                location,
                            )
                    elif after_hyphen:
                        raise errors.InterfaceError(
                            "hyphen (-) must be followed by number but found: %s" % _compat.text_repr(next_value),
                            location,
                        )
                    elif (next_type == token.OP) and (next_value == "-"):
                        after_hyphen = True
                    elif next_value in (ELLIPSIS, ":"):
                        ellipsis_found = True
                    else:
                        raise errors.InterfaceError(
                            "range must be specified using integer numbers, text, "
                            "symbols and ellipsis (...) but found: %s [token type: %d]"
                            % (_compat.text_repr(next_value), next_type),
                            location,
                        )
                    next_token = next(tokens)

                if after_hyphen:
                    raise errors.InterfaceError("hyphen (-) at end must be followed by number", location)

                # Decide upon the result.
                if lower is None:
                    if upper is None:
                        if ellipsis_found:
                            # Handle "...".
                            raise errors.InterfaceError(
                                "ellipsis (...) must be preceded and/or succeeded by number", location
                            )
                        else:
                            # Handle "".
                            result = None
                    else:
                        assert ellipsis_found
                        # Handle "...y".
                        result = (None, upper)
                elif ellipsis_found:
                    # Handle "x..." and "x...y".
                    if (upper is not None) and (lower > upper):
                        raise errors.InterfaceError(
                            "lower range %d must be greater or equal than upper range %d" % (lower, upper), location
                        )
                    result = (lower, upper)
                else:
                    # Handle "x".
                    result = (lower, lower)
                if result is not None:
                    for item in self._items:
                        if self._items_overlap(item, result):
                            item_text = _compat.text_repr(self._repr_item(item))
                            result_text = _compat.text_repr(self._repr_item(result))
                            raise errors.InterfaceError(
                                "overlapping parts in range must be cleaned up: %s and %s" % (item_text, result_text),
                                location,
                            )
                    self._items.append(result)
                if _tools.is_eof_token(next_token):
                    end_reached = True

            self._lower_limit = None
            self._upper_limit = None
            is_first_item = True
            for lower_item, upper_item in self._items:
                if is_first_item:
                    self._lower_limit = lower_item
                    self._upper_limit = upper_item
                    is_first_item = False

                if lower_item is None:
                    self._lower_limit = None
                elif (self._lower_limit is not None) and (lower_item < self._lower_limit):
                    self._lower_limit = lower_item

                if upper_item is None:
                    self._upper_limit = None
                elif (self._upper_limit is not None) and (upper_item > self._upper_limit):
                    self._upper_limit = upper_item

    @property
    def description(self):
        """
        The original human readable description of the range used to construct it.
        """
        return self._description

    @property
    def items(self):
        """
        A list derived from :py:attr:`~cutplace.ranges.Range.description` for
        fast processing. Each item is represented by a tuple
        ``(lower, upper)`` where both of ``lower`` or ``upper`` can be
        ``None``. For example, ``'2...20'`` becomes ``(2, 20)``, ``'...20'``
        becomes ``(None, 20)`` and ``'2...'`` becomes ``(2, None)``.

        :rtype: list
        """
        return self._items

    @property
    def lower_limit(self):
        """
        The minimum of :py:attr:`~cutplace.ranges.Range.items` or ``None`` if
        any of them is ``None`` (meaning there is no lower bound).

        :rtype: int
        """
        return self._lower_limit

    @property
    def upper_limit(self):
        """
        The maximum of :py:attr:`~cutplace.ranges.Range.items` or ``None`` if
        any of them is ``None`` (meaning there is no upper bound).

        :rtype: int
        """
        return self._upper_limit

    def _repr_item(self, item):
        """
        Human readable description of a range item.
        """
        if item is not None:
            result = ""
            (lower, upper) = item
            if lower is None:
                assert upper is not None
                result += "...%s" % upper
            elif upper is None:
                result += "%s..." % lower
            elif lower == upper:
                result += "%s" % lower
            else:
                result += "%s...%s" % (lower, upper)
        else:
            result = str(None)
        return result

    def __repr__(self):
        """
        Human readable description of the range similar to a Python tuple.
        """
        return "Range('%s')" % self

    def __str__(self):
        """
        Human readable description of the range similar to a Python tuple.
        """
        if self.items:
            result = ""
            is_first = True
            for item in self._items:
                if is_first:
                    is_first = False
                else:
                    result += ", "
                result += self._repr_item(item)
        else:
            result = str(None)
        return result

    def _items_overlap(self, some, other):
        assert some is not None
        assert len(some) == 2
        assert some != (None, None)
        assert other is not None
        assert len(other) == 2
        assert other != (None, None)

        lower, upper = other
        result = self._item_contains(some, lower) or self._item_contains(some, upper)
        return result

    def _item_contains(self, item, value):
        assert item is not None
        assert len(item) == 2
        assert item != (None, None)

        result = False
        if value is not None:
            lower, upper = item
            if lower is None:
                assert upper is not None
                # Handle "...y"
                result = value <= upper
            elif upper is None:
                # Handle "x..."
                result = value >= lower
            else:
                # Handle "x...y"
                result = (value >= lower) and (value <= upper)
        return result

    def validate(self, name, value, location=None):
        """
        Validate that ``value`` is within the specified range.

        :param str name: the name of ``value`` known to the end user for \
          usage in possible error messages
        :param int value: the value to validate
        :param cutplace.errors.Location location: the location to refer to \
          in possible error messages
        :raises cutplace.errors.RangeValueError: if ``value`` is out of range
        """
        assert name is not None
        assert name
        assert value is not None

        if self._items is not None:
            is_valid = False
            item_index = 0
            while not is_valid and item_index < len(self._items):
                lower, upper = self._items[item_index]
                if lower is None:
                    assert upper is not None
                    if value <= upper:
                        is_valid = True
                elif upper is None:
                    if value >= lower:
                        is_valid = True
                elif (value >= lower) and (value <= upper):
                    is_valid = True
                item_index += 1
            if not is_valid:
                raise errors.RangeValueError("%s is %r but must be within range: %s" % (name, value, self), location)


class DecimalRange(Range):
    """
    A decimal range to validate that decimal values are within it.

    Example:

    >>> from cutplace.ranges import DecimalRange
    >>> size_range = DecimalRange('0...299.99')
    >>> size_range.scale
    5
    >>> size_range.precision
    2
    >>> size_range.validate('size', '1.72')
    >>> size_range.validate('size', '1234.56')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    cutplace.errors.RangeValueError: size is Decimal('1234.56') but must be within range: '0.00...299.99'
    """

    def __init__(self, description, default=None, location=None):
        """
        Setup a decimal range as specified by ``description``.

        :param str description: a range description of the form \
          ``lower...upper`` or ``limit``, possibly consisting of multiple \
          items. In case it is empty (``''``), the range specified by \
          ``default`` is used; the description also specifies the \
          :py:attr:`~cutplace.ranges.DecimalRange.scale` and \
          :py:attr:`~cutplace.ranges.DecimalRange.precision` valid numbers \
          can use.
        :param str default: an alternative to use in case ``description``
          is ``None`` or empty; in case both ``description`` and \
          ``default`` are ``None`` or empty, all values within the \
          :py:const:`DEFAULT_SCALE` and :py:const:`DEFAULT_PRECISION` are \
          valid.

        """
        assert default is None or (default.strip() != ""), "default=%r" % default

        self._precision = DEFAULT_PRECISION
        self._scale = DEFAULT_SCALE

        # Find out if a `description` has been specified and if not, use optional `default` instead.
        has_description = (description is not None) and (description.strip() != "")
        if not has_description and default is not None:
            description = default
            has_description = True

        if not has_description:
            # Use empty ranges.
            self._description = None
            self._items = None
            self._lower_limit = None
            self._upper_limit = None
        else:
            self._description = description.replace("...", ELLIPSIS)
            self._items = []
            tokens = _tools.tokenize_without_space(self._description)
            end_reached = False
            max_digits_after_dot = 0
            max_digits_before_dot = 0
            while not end_reached:
                lower = None
                upper = None
                ellipsis_found = False
                after_hyphen = False
                next_token = next(tokens)
                while not _tools.is_eof_token(next_token) and not _tools.is_comma_token(next_token):
                    next_type = next_token[0]
                    next_value = next_token[1]
                    if next_type == token.NUMBER:
                        if next_type == token.NUMBER:
                            try:
                                decimal_value = decimal.Decimal(next_value)
                                _, digits, exponent = decimal_value.as_tuple()
                                digits_after_dot = max(0, -exponent)
                                if digits_after_dot > max_digits_after_dot:
                                    max_digits_after_dot = digits_after_dot
                                digits_before_dot = len(digits) + exponent
                                if digits_before_dot > max_digits_before_dot:
                                    max_digits_before_dot = digits_before_dot
                            except decimal.DecimalException:
                                raise errors.InterfaceError(
                                    "number must be an decimal or integer but is: %s" % _compat.text_repr(next_value),
                                    location,
                                )
                            if after_hyphen:
                                decimal_value = decimal_value.copy_negate()
                                after_hyphen = False

                        if ellipsis_found:
                            if upper is None:
                                upper = decimal_value
                            else:
                                raise errors.InterfaceError(
                                    "range must have at most lower and upper limit but found another number: %s"
                                    % _compat.text_repr(next_value),
                                    location,
                                )
                        elif lower is None:
                            lower = decimal_value
                        else:
                            raise errors.InterfaceError(
                                "number must be followed by ellipsis (...) but found: %s"
                                % _compat.text_repr(next_value)
                            )
                    elif after_hyphen:
                        raise errors.InterfaceError(
                            "hyphen (-) must be followed by number but found: %s" % _compat.text_repr(next_value)
                        )
                    elif (next_type == token.OP) and (next_value == "-"):
                        after_hyphen = True
                    elif next_value in (ELLIPSIS, ":"):
                        ellipsis_found = True
                    else:
                        message = (
                            "range must be specified using decimal or integer numbers"
                            " and ellipsis (...) but found: %s [token type: %d]"
                            % (_compat.text_repr(next_value), next_type)
                        )
                        raise errors.InterfaceError(message)
                    next_token = next(tokens)

                if after_hyphen:
                    raise errors.InterfaceError("hyphen (-) at end must be followed by number")

                # Decide upon the result.
                if lower is None:
                    if upper is None:
                        if ellipsis_found:
                            # Handle "...".
                            # TODO: Handle "..." same as ""?
                            raise errors.InterfaceError("ellipsis (...) must be preceded and/or succeeded by number")

                    else:
                        assert ellipsis_found
                        # Handle "...y".
                        range_item = (None, upper)
                elif ellipsis_found:
                    # Handle "x..." and "x...y".
                    if (upper is not None) and (lower > upper):
                        raise errors.InterfaceError(
                            "lower limit %s must be less or equal than upper limit %s"
                            % (_decimal_as_text(lower, self.precision), _decimal_as_text(upper, self.precision))
                        )
                    range_item = (lower, upper)
                else:
                    # Handle "x".
                    range_item = (lower, lower)
                if range_item is not None:
                    self._precision = max_digits_after_dot
                    self._scale = max_digits_before_dot + max_digits_after_dot
                    for item in self._items:
                        if self._items_overlap(item, range_item):
                            item_text = _compat.text_repr(self._repr_item(item))
                            result_text = _compat.text_repr(self._repr_item(range_item))
                            raise errors.InterfaceError(
                                "overlapping parts in decimal range must be cleaned up: %s and %s"
                                % (item_text, result_text),
                                location,
                            )
                    self._items.append(range_item)
                if _tools.is_eof_token(next_token):
                    end_reached = True

            assert self.precision >= 0
            assert self.scale >= self.precision

            self._lower_limit = None
            self._upper_limit = None
            is_first_item = True
            for lower_item, upper_item in self._items:
                if is_first_item:
                    self._lower_limit = lower_item
                    self._upper_limit = upper_item
                    is_first_item = False

                if lower_item is None:
                    self._lower_limit = None
                elif (self._lower_limit is not None) and (lower_item < self._lower_limit):
                    self._lower_limit = lower_item

                if upper_item is None:
                    self._upper_limit = None
                elif (self._upper_limit is not None) and (upper_item > self._upper_limit):
                    self._upper_limit = upper_item

    @property
    def precision(self):
        return self._precision

    @property
    def scale(self):
        return self._scale

    def __repr__(self):
        """
        Human readable description of the range similar to a Python tuple.
        """
        if self.items:
            result = "'%s'" % self
        else:
            result = str(None)
        return result

    def __str__(self):
        """
        Human readable description of the range similar to a Python tuple.
        """
        if self.items:
            result = ""
            is_first = True
            for item in self._items:
                if is_first:
                    is_first = False
                else:
                    result += ", "
                result += self._repr_item(item)
        else:
            result = str(None)
        return result

    def _repr_item(self, item):
        """
        Human readable description of a range item.
        """
        if item is not None:
            result = ""
            (lower, upper) = item
            if lower is None:
                assert upper is not None
                result += _decimal_as_text(upper, self.precision)
            else:
                result += _decimal_as_text(lower, self.precision)
                if upper is not None:
                    result += "..." + _decimal_as_text(upper, self.precision)
        else:
            result = str(None)
        return result

    def validate(self, name, value, location=None):
        """
        Validate that ``value`` is within the specified range.

        :param str name: the name of ``value`` known to the end user for \
          usage in possible error messages
        :param int value: the value to validate
        :param cutplace.errors.Location location: the location to refer to \
          in possible error messages
        :raises cutplace.errors.RangeValueError: if ``value`` is out of range
        """
        assert name is not None
        assert name
        assert value is not None

        if not isinstance(value, decimal.Decimal):
            try:
                value_as_decimal = decimal.Decimal(value)
            except decimal.DecimalException:
                raise errors.RangeValueError("value must be decimal but is %s" % _compat.text_repr(value), location)
        else:
            value_as_decimal = value

        if self._items is not None:
            is_valid = False
            item_index = 0
            while not is_valid and item_index < len(self._items):
                lower, upper = self._items[item_index]
                if lower is None:
                    assert upper is not None
                    if value_as_decimal <= upper:
                        is_valid = True
                elif upper is None:
                    if value_as_decimal >= lower:
                        is_valid = True
                elif (value_as_decimal >= lower) and (value_as_decimal <= upper):
                    is_valid = True
                item_index += 1
            if not is_valid:
                raise errors.RangeValueError(
                    "%s is %r but must be within range: %r" % (name, value_as_decimal, self), location
                )
