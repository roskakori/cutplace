"""
Ranges check if certain values are within it. This is used in several places of the ICD, in
particular to specify the length limits for field values and the characters allowed for a data
format.
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
import StringIO
import token
import tokenize

import tools
import _tools


class RangeSyntaxError(tools.CutplaceError):
    """
    Error in Range declaration.
    """


class RangeValueError(tools.CutplaceError):
    """
    Error raised when ranges.validate() detects that a value is outside the expected ranges.
    """


class Range(object):
    """
    A range that can be used to validate that a value is within it.
    """

    def __init__(self, text, default=None):
        """
        Setup a range as specified by ``text``.

        ``text`` must be of the form "lower:upper" or "limit". In case ``text`` is empty (""), any
        value will be accepted by `validate()`. For example, "1:40" accepts values between 1
        and 40.

        ``default`` is an alternative text to use in case ``text`` is ``None`` or empty.
        """
        assert default is None or default.strip(), u"default=%r" % default

        # Find out if a `text` has been specified and if not, use optional `default` instead.
        hasText = (text is not None) and text.strip()
        if not hasText and default is not None:
            text = default
            hasText = True

        if not hasText:
            # Use empty ranges.
            self._description = None
            self._items = None
        else:
            self._description = text
            self._items = []
            # TODO: Consolidate code with `DelimitedDataFormat._validatedCharacter()`.
            tokens = tokenize.generate_tokens(StringIO.StringIO(text).readline)
            endReached = False
            while not endReached:
                lower = None
                upper = None
                colonFound = False
                afterHyphen = False
                nextToken = tokens.next()
                while not _tools.isEofToken(nextToken) and not _tools.isCommaToken(nextToken):
                    nextType = nextToken[0]
                    nextValue = nextToken[1]
                    if nextType in (token.NAME, token.NUMBER, token.STRING):
                        if nextType == token.NUMBER:
                            try:
                                if nextValue[:2].lower() == "0x":
                                    nextValue = nextValue[2:]
                                    base = 16
                                else:
                                    base = 10
                                longValue = long(nextValue, base)
                            except ValueError:
                                raise RangeSyntaxError(u"number must be an integer but is: %r" % nextValue)
                            if afterHyphen:
                                longValue = - 1 * longValue
                                afterHyphen = False
                        elif nextType == token.NAME:
                            try:
                                longValue = tools.SYMBOLIC_NAMES_MAP[nextValue.lower()]
                            except KeyError:
                                validSymbols = _tools.humanReadableList(sorted(tools.SYMBOLIC_NAMES_MAP.keys()))
                                raise RangeSyntaxError(u"symbolic name %r must be one of: %s" % (nextValue, validSymbols))
                        elif nextType == token.STRING:
                            if len(nextValue) != 3:
                                raise RangeSyntaxError(u"text for range must contain a single character but is: %r" % nextValue)
                            leftQuote = nextValue[0]
                            rightQuote = nextValue[2]
                            assert leftQuote in "\"\'", u"leftQuote=%r" % leftQuote
                            assert rightQuote in "\"\'", u"rightQuote=%r" % rightQuote
                            longValue = ord(nextValue[1])
                        if colonFound:
                            if upper is None:
                                upper = longValue
                            else:
                                raise RangeSyntaxError("range must have at most lower and upper limit but found another number: %r" % nextValue)
                        elif lower is None:
                            lower = longValue
                        else:
                            raise RangeSyntaxError(u"number must be followed by colon (:) but found: %r" % nextValue)
                    elif afterHyphen:
                        raise RangeSyntaxError(u"hyphen (-) must be followed by number but found: %r" % nextValue)
                    elif (nextType == token.OP) and (nextValue == "-"):
                        afterHyphen = True
                    elif (nextType == token.OP) and (nextValue == ":"):
                        if colonFound:
                            raise RangeSyntaxError(u"range item must contain at most one colon (:)")
                        colonFound = True
                    else:
                        message = u"range must be specified using integer numbers, text, symbols and colon (:) but found: %r [token type: %r]" % (nextValue, nextType)
                        raise RangeSyntaxError(message)
                    nextToken = tokens.next()
                if afterHyphen:
                    raise RangeSyntaxError(u"hyphen (-) at end must be followed by number")

                # Decide upon the result.
                if (lower is None):
                    if (upper is None):
                        if colonFound:
                            # Handle ":".
                            # TODO: Handle ":" same as ""?
                            raise RangeSyntaxError(u"colon (:) must be preceded and/or succeeded by number")
                        else:
                            # Handle "".
                            result = None
                    else:
                        assert colonFound
                        # Handle ":y".
                        result = (None, upper)
                elif colonFound:
                    # Handle "x:" and "x:y".
                    if (upper is not None) and (lower > upper):
                        raise RangeSyntaxError(u"lower range %d must be greater or equal to upper range %d" % (lower, upper))
                    result = (lower, upper)
                else:
                    # Handle "x".
                    result = (lower, lower)
                if result is not None:
                    for item in self._items:
                        if self._itemsOverlap(item, result):
                            # TODO: use _repr_item() or something to display item in error message.
                            raise RangeSyntaxError(u"range items must not overlap: %r and %r"
                                                   % (self._repr_item(item), self._repr_item(result)))
                    self._items.append(result)
                if _tools.isEofToken(nextToken):
                    endReached = True

    @property
    def description(self):
        """
        The original human readable description of the range used to construct it.
        """
        return self._description

    @property
    def items(self):
        """
        A list compiled from `description` for fast processing. Each item is represented by a
        tuple ``(lower, upper)`` where either ``lower``or ``upper`` can be ``None``. For example,
        "2:20" turns ``(2, 20)``, ":20" turns to ``(None, 20)`` and "2:" becomes ``(2, None)``.
        """
        return self._items

    def _repr_item(self, item):
        """
        Human readable description of a range item.
        """
        if item is not None:
            result = ""
            (lower, upper) = item
            if lower is None:
                assert upper is not None
                result += ":%s" % upper
            elif upper is None:
                result += "%s:" % lower
            elif lower == upper:
                result += "%s" % lower
            else:
                result += "%s:%s" % (lower, upper)
        else:
            result = str(None)
        return result

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
            isFirst = True
            for item in self._items:
                if isFirst:
                    isFirst = False
                else:
                    result += ", "
                result += self._repr_item(item)
        else:
            result = str(None)
        return result

    def _itemsOverlap(self, some, other):
        assert some is not None
        assert other is not None
        lower = other[0]
        upper = other[1]
        result = self._itemContains(some, lower) or self._itemContains(some, upper)
        return result

    def _itemContains(self, item, value):
        assert item is not None
        result = False
        if value is not None:
            lower = item[0]
            upper = item[1]
            if lower is None:
                if upper is None:
                    # Handle ""
                    result = True
                else:
                    # Handle ":y"
                    result = (value <= upper)
            elif upper is None:
                # Handle "x:"
                result = (value >= lower)
            else:
                # Handle "x:y"
                result = (value >= lower) and (value <= upper)
        return result

    def validate(self, name, value):
        """
        Validate that value is within the specified range and in case it is not, raise a `RangeValueError`.
        """
        assert name is not None
        assert name
        assert value is not None

        if self._items is not None:
            isValid = False
            itemIndex = 0
            while not isValid and itemIndex < len(self._items):
                lower, upper = self._items[itemIndex]
                if lower is None:
                    assert upper is not None
                    if value <= upper:
                        isValid = True
                elif upper is None:
                    if value >= lower:
                        isValid = True
                elif (value >= lower) and (value <= upper):
                    isValid = True
                itemIndex += 1
            if not isValid:
                raise RangeValueError(u"%s is %r but must be within range: %r" % (name, value, self))
