"""
Range to check if certain values are within it. This is used in several places of the ICD, in 
particular to specify the length limits for field values.
"""
import StringIO
import token
import tokenize
import tools

class RangeSyntaxError(tools.CutplaceError):
    """
    Error in Range declaration.
    """
    pass

class RangeValueError(tools.CutplaceError):
    """
    Error raised when Range.validate() detects that a value is outside the expected range.
    """
    pass

class Range(object):
    def __init__(self, text):
        """
        Assume text is of the form "lower:upper" or "[value]" and return (lower, upper) respectively (value, value).
        In case text is empty (""), return None.
        """
        assert text is not None
        self.description = text
        self.items = []
        lower = None
        upper = None
        colonFound = False
        afterHyphen = False
        tokens = tokenize.generate_tokens(StringIO.StringIO(text).readline)
        next = tokens.next()
        while not tokenize.ISEOF(next[0]):
            nextType = next[0]
            nextValue = next[1]
            if nextType == token.NUMBER:
                longValue = long(nextValue)
                if afterHyphen:
                    longValue = - 1 * longValue
                    afterHyphen = False
                if colonFound:
                    if upper is None:
                        upper = longValue
                    else:
                        raise RangeSyntaxError("range must have at most lower and upper limit but found another number: %r" % nextValue)
                elif lower is None:
                    lower = longValue
                else:
                    raise RangeSyntaxError("number must be followed by colon (:) but found: %r" % nextValue)
            elif afterHyphen:
                raise RangeSyntaxError("hyphen (-) must be followed by number but found: %r" % nextValue)
            elif (nextType == token.OP) and (nextValue == "-"):
                afterHyphen = True
            elif (nextType == token.OP) and (nextValue == ":"):
                if colonFound:
                    raise RangeSyntaxError("range item must contain at most one colon (:)")
                colonFound = True
            else:
                message = "range must be specified using integer numbers and colon (:) but found: %r" % nextValue
                if __debug__:
                    message += " (token type: %r)" % nextType
                raise RangeSyntaxError("range must be specified using integer numbers and colon (:) but found: %r (%r)" % (nextValue, nextType))
            next = tokens.next()
        if afterHyphen:
            raise RangeSyntaxError("hyphen (-) at end must be followed by number")
        
        # Decide upon the result.
        if (lower is None):
            if (upper is None):
                if colonFound:
                    # Handle ":".
                    raise RangeSyntaxError("colon (:) must be preceeded and/or suceeded by number")
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
                raise RangeSyntaxError("lower range %d must be greater or equal to upper range %d" % (lower, upper))
            result = (lower, upper)
        else:
            # Handle "x".
            result = (lower, lower)
        if result is not None:
            self.items.append(result)
        
    def validate(self, name, value):
        """
        Validate that value is within the specified range and in case it is not, raise a RangeValueError.
        """
        assert name is not None
        assert name
        assert value is not None

        isValid = False
        itemIndex = 0
        while not isValid and itemIndex < len(self.items):
            lower, upper = self.items[itemIndex]
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
            raise RangeValueError("%s is %r but must bi within range: %r" % (name, value, self.items))
        