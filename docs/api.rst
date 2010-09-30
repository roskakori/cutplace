================================
Application programmer interface
================================

Overview
========

Additionally to the command line tool ``cutplace`` all functions are available
as Python API. For a complete reference about all public classes and functions,
visit <http://cutplace.sourceforge.net/api/>.

The remainder of this chapter focuses on describing how to perform a basic
validation of a simple CSV file containing data about some customers.

Set up logging
==============

Cutplace uses Python's standard logging module. This provides a familiar and
powerful way to watch what cutplace is doing. However, it also requires to
setup the logging properly in order to gain most from it.

For a quick start, set up your application's log messages to go to the console
and show only information, warning and errors, but no debug messages:

>>> import logging
>>> logging.basicConfig(level=logging.INFO)

Next trim cutplace's logging to show only warnings and errors as you might not
be particularly interested in whatever it is cutplace does during a
validation:

>>> logging.getLogger("cutplace").setLevel(logging.WARNING)

This should be enough to get you going. To learn more about logging, take a
look at `logging chapter <http://docs.python.org/library/logging.html>`_ of
the Python library documentation.

Read or build an ICD
====================

The class
`interface.InterfaceControlDocument <api/cutplace.interface.InterfaceControlDocument-class.html>`_
represents an ICD. In case you have an ICD stored in a file and want to read
it, use:

>>> import os.path
>>> from cutplace import interface
>>>
>>> # Compute the path of a test file in a system independent manner.
>>> icdPath = os.path.join("tests", "input", "icds", "customers.csv")
>>>
>>> icd = interface.InterfaceControlDocument()
>>> icd.read(icdPath)
>>> icd.fieldNames
[u'branch_id', u'customer_id', u'first_name', u'surname', u'gender', u'date_of_birth']

This is the easiest way, which also keeps declaration and validation in
separate files.

In some cases it might be preferable to include the ICD in the code, for
instance for trivial interfaces that are only used internally. Here is an
example of a simple ICD for CSV data with 3 fields:

>>> from cutplace import data
>>> from cutplace import fields
>>> from cutplace import interface
>>>
>>> icd = interface.InterfaceControlDocument()

As the ICD will not be read from an input file, error messages would not be
able to refer to any file in case of errors. To have at least some reference,
we need to tell the ICD that it is declared from source code:

>>> icd.setLocationToSourceCode()

That way, error messages will refer you to the Python module where this call
happened.

>>> # Use CSV as data format. This is the same as having a spreadsheet
>>> # with the cells:
>>> #
>>> # | F | Format         | CSV |
>>> # | F | Item separator | ;   |
>>> icd.addDataFormat([data.KEY_FORMAT, data.FORMAT_CSV])
>>> icd.addDataFormat([data.KEY_ITEM_DELIMITER, ";"])
>>>
>>> # Add a couple of fields.
>>> icd.addFieldFormat(["id", "", "", "1:5", "Integer"])
>>> icd.addFieldFormat(["name"])
>>> icd.addFieldFormat(["dateOfBirth", "", "X", "", "DateTime", "YYYY-MM-DD"])
>>>
>>> # Make sure that the `id` field contains only unique values.
>>> icd.addCheck(["id_must_be_unique", "IsUnique", "id"])

>>> icd.fieldNames
['id', 'name', 'dateOfBirth']

If any of this methods cannot handle the parameters you passed, the raise a
``CutplaceError`` with a message describing what went wrong.

>>> icd.addCheck([])
Traceback (most recent call last):
    ...
CheckSyntaxError: <source> (R1C2): check row (marked with 'f') must contain at least 2 columns

Validate data
=============

Once the ICD is set up, you can validate data using ``validate()``:

>>> icdPath = os.path.join("tests", "input", "icds", "customers.csv")
>>> icd = interface.InterfaceControlDocument()
>>> icd.read(icdPath)
>>>
>>> validCsvPath = os.path.join("tests", "input", "valid_customers.csv")
>>> icd.validate(validCsvPath)

So what happens if the data contain errors? Let's give it a try:

>>> brokenCsvPath = os.path.join("tests", "input", "broken_customers.csv")
>>> icd.validate(brokenCsvPath)

Again, the validation runs through without any ``Exception`` or other
indication that something is wrong.

The reason for that is that cutplace should be able to continue in case a data
row is rejected. Raining an ``Exception`` would defeat that. So instead, it
informs interested listeners about validation events. To act on events, define
a class inheriting from ``BaseValidationListener`` and overwrite the methods
for the events you are interested in:

>>> class ErrorPrintingValidationListener(interface.BaseValidationListener):
...     def rejectedRow(self, row, error):
...         print "%r" % row
...         print "error: %s" % error

This is a very simple listener which is only interested about rejected rows. In
case this happens, it simply prints the row and the error that was detected in it.
To learn about other events this listener can receive, take a look at the API
documentation of
`BaseValidationListener <api/cutplace.interface.BaseValidationListener-class.html>`_

To actually get some information about validation errors, you have to create
such a listener and attach it to an ICD:

>>> errorPrintingValidationListener = ErrorPrintingValidationListener()
>>> icd.addValidationListener(errorPrintingValidationListener)

Let's see what happens if we validate broken data again:

>>> icd.validate(brokenCsvPath)
[u'12345', u'92', u'Bill', u'Carter', u'male', u'05.04.1953']
error: field u'branch_id' must match format: value u'12345' must match regular expression: u'38\\d\\d\\d'
[u'38111', u'XX', u'Sue', u'Brown', u'female', u'08.02.1962']
error: field u'customer_id' must match format: value must be an integer number: u'XX'
[u'38088', u'83', u'Rose', u'Baker', u'female', u'30.02.1994']
error: field u'date_of_birth' must match format: date must match format DD.MM.YYYY (%d.%m.%Y) but is: u'30.02.1994' (day is out of range for month)

When you are done, remove the listener::

>>> icd.removeValidationListener(errorPrintingValidationListener)

Putting it all together
=======================

You now know how to:

* declare and ICD in the source code
* validate data from a file
* listen to event happening during validation

All that is left to do is to collect the code snipplets of the previous sections
in one example you can use as base for your own validation code:

>>> # Validate a test CSV file.
>>> import os.path
>>> from cutplace import interface
>>> # Define a listener for validation events.
>>> class ErrorPrintingValidationListener(interface.BaseValidationListener):
...     def rejectedRow(self, row, error):
...         print "%r" % row
...         print "error: %s" % error
>>> # Change this to use your own files.
>>> icdPath = os.path.join("tests", "input", "icds", "customers.csv")
>>> dataPath = os.path.join("tests", "input", "broken_customers.csv")
>>> # Define the interface.
>>> icd = interface.InterfaceControlDocument()
>>> icd.read(icdPath)
>>> # Validate the data.
>>> errorPrintingValidationListener = ErrorPrintingValidationListener()
>>> icd.addValidationListener(errorPrintingValidationListener)
>>> try:
...     icd.validate(brokenCsvPath)
... finally:
...     icd.removeValidationListener(errorPrintingValidationListener)
[u'12345', u'92', u'Bill', u'Carter', u'male', u'05.04.1953']
error: field u'branch_id' must match format: value u'12345' must match regular expression: u'38\\d\\d\\d'
[u'38111', u'XX', u'Sue', u'Brown', u'female', u'08.02.1962']
error: field u'customer_id' must match format: value must be an integer number: u'XX'
[u'38088', u'83', u'Rose', u'Baker', u'female', u'30.02.1994']
error: field u'date_of_birth' must match format: date must match format DD.MM.YYYY (%d.%m.%Y) but is: u'30.02.1994' (day is out of range for month)

Writing field formats
=====================

Cutplace already ships with several field formats that should cover most needs.
If however you have some very special requirements, you can write your own
formats.

The easiest way to do so is by adding your format to ``cutplace/fields.py``.
Simply inherit from ``AbstractFieldFormat`` and optionally provide a
constructor to parse the ``rule`` parameter. Next, implement
``validatedValue(self, value)`` that validates that the text in ``value``
conforms to ``rule``. If not, raise an ``FieldValueError`` with a descriptive
error message.

Here is a very simple example of a field format that accepts values of "red",
"green" and "blue".

>>> class ColorFieldFormat(fields.AbstractFieldFormat):
...     def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
...         super(ColorFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
...
...     def validatedValue(self, value):
...         # Validate that ``value`` is a color and return it.
...         assert value
...         if value not in ["red", "green", "blue"]:
...             raise fields.FieldValueError("color value is %r but must be one of: red, green, blue" % value)
...         return value

The ``value`` parameter is a Unicode string. Cutplace ensures that
``validatedValue()`` will never be called with an empty ``value`` parameter,
hence the ``assert value`` - it will cause an ``AssertionError`` if ``value``
is ``""`` or ``None`` because that would mean cutplace is broken.

>>> colorField = ColorFieldFormat("roofColor", False, "", "", icd.dataFormat)
>>> colorField.validated("red")
'red'

Of course you have achieved they same thing using `fields.ChoiceFieldFormat
<api/fields.ChoiceFieldFormat-class.html>`_. However, a custom field format can
do more. In particular, ``validatedValue()`` does not have to return a string.
It can return any Python type and even ``None``. The result will be used in the
``row`` array cutplace sends to any `BaseValidationListener.acceptedRow()
<api/cutplace.interface.BaseValidationListener-class.html#acceptedRow>`_.

Here's a more advanced ``ColorFieldFormat`` that returns the color as a
tuple of RGB items:

>>> class ColorFieldFormat(fields.AbstractFieldFormat):
...     def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
...         super(ColorFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat, emptyValue="")
...
...     def validatedValue(self, value):
...         # Validate that ``value`` is a color and return its RGB representation.
...         assert value
...         if value == "red":
...             result = (1.0, 0.0, 0.0)
...         elif value == "green":
...             result = (0.0, 1.0, 0.0)
...         elif value == "green":
...             result = (0.0, 1.0, 0.0)
...         else:
...             raise fields.FieldValueError("color value is %r but must be one of: red, green, blue" % value)
...         return result



For a simple test, let's see this field format in action:

>>> colorField = ColorFieldFormat("roofColor", False, "", "", icd.dataFormat)
>>> colorField.validated("red")
(1.0, 0.0, 0.0)
>>> colorField.validated("yellow")
Traceback (most recent call last):
...
FieldValueError: color value is 'yellow' but must be one of: red, green, blue

Before you learned that ``validatedValue()`` never gets called with an empty
value. So what happens if you declare a color field that allows empty values,
for instance:

>>> # Sets ``isAllowedToBeEmpty`` to ``True`` to accept empty values.
>>> colorField = ColorFieldFormat("roofColor", True, "", "", icd.dataFormat)
>>> colorField.validated("")
''
>>> # Not quiet a color tuple...

Well, that's not quite what we want. Instead of an empty string, some default
RGB tuple would be a lot more useful. Say, ``(0.0, 0.0, 0.0)`` to represent
black.

Fortunately field formats can just specify that by using the ``emptyValue``
parameter in the constructor. When passed to the ``super`` constructor in
``AbstractFieldFormat``, everything will be taken care of. So here's a
slightly modified version:

>>> class ColorFieldFormat(fields.AbstractFieldFormat):
...     def __init__(self, fieldName, isAllowedToBeEmpty, length, rule, dataFormat):
...         super(ColorFieldFormat, self).__init__(fieldName, isAllowedToBeEmpty, length, rule, dataFormat,
...                 emptyValue=(0.0, 0.0, 0.0)) # Use black as "empty" color.
...
...     def validatedValue(self, value):
...         # (Exactly same as before)
...         assert value
...         if value == "red":
...             result = (1.0, 0.0, 0.0)
...         elif value == "green":
...             result = (0.0, 1.0, 0.0)
...         elif value == "green":
...             result = (0.0, 1.0, 0.0)
...         else:
...             raise fields.FieldValueError("color value is %r but must be one of: red, green, blue" % value)
...         return result

Let's give it a try:

>>> colorField = ColorFieldFormat("roofColor", True, "", "", icd.dataFormat)
>>> colorField.validated("red")
(1.0, 0.0, 0.0)
>>> colorField.validated("")
(0.0, 0.0, 0.0)

Now that you know how to write your own field format, it would be nice to
actually utilize it in an ICD.

TODO: Describe how to write a ``myfields.py`` and extend the Python path.

Writing checks
==============

Writing checks is quite similar to writing field formats. The standard checks
are stored in ``cutplace/checks.py``. Inherit from ``AbstractCheck`` and
provide a constructor. You might want to implement at least one of the
following methods:

* ``checkRow(self, rowNumber, row)``: called for each row read from the data.
  ``RowNumber`` is useful to report errors, row is a list where each item
  contains the value from one column as found in the input data.

* ``checkAtEnd(self)``: called when all rows from the data are processed.

In case the check discovers any issues, it should raise a ``CheckError``.

TODO: Describe how to write mychecks.py and extend Python path.
