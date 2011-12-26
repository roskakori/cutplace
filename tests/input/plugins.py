"""
Plugins to be used for tests.
"""
try:
    # HACK: Import used when launched from shell or eclipse.
    import fields
except ImportError:
    # HACK: Import used when launched from ant.
    from cutplace import fields

class CapitalizedTextFieldFormat(fields.AbstractFieldFormat):
    """
    Field format to validate for ``value`` to start in upper case. This is used test plugin support.
    """
    def validatedValue(self, value):
        if value:
            firstChar = value[0]
            if not firstChar.isupper():
                raise fields.FieldValueError(u"first character %r must be changed to upper case: %r" % (firstChar, value))
        return value
