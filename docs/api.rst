.. index:: API, application programmer interface

================================
Application programmer interface
================================

Overview
========

Additionally to the command line tool :command:`cutplace` all functions are
available as Python API. For a complete reference about all public classes
and functions, refer to the :ref:`modindex`.

This chapter describes how to perform a basic validation of a simple CSV file
containing data about some customers. It also explains how to extend
cutplace's fields formats and checks and implement your own.


Logging
=======

Cutplace uses Python's standard :py:mod:`logging` module. This provides a
familiar and powerful way to watch what cutplace is doing. However, it also
requires to setup the logging properly in order to gain most from it.

For a quick start, set up your application's log messages to go to the console
and show only information, warning and errors, but no debug messages::

    >>> import logging
    >>> logging.basicConfig(level=logging.INFO)

Next trim cutplace's logging to show only warnings and errors as you might not
be particularly interested in whatever it is cutplace does during a
validation::

    >>> logging.getLogger('cutplace').setLevel(logging.WARNING)

This should be enough to get you going. To learn more about logging, take a
look at `logging chapter <http://docs.python.org/library/logging.html>`_ of
the Python library documentation.


Basic usage
===========


Reading a CID
-------------

The class :py:mod:`cutplace.Cid` represents a CID. In case you have a CID
stored in a file and want to read it, use::

    >>> import os.path
    >>> import cutplace
    >>>
    >>> # Compute the path of a test file in a system independent manner,
    >>> # assuming that the current folder is "docs".
    >>> cid_path = os.path.join(os.pardir, 'tests', 'data', 'cids', 'customers.ods')
    >>> cid = cutplace.Cid(cid_path)
    >>> cid.field_names
    ['branch_id', 'customer_id', 'first_name', 'surname', 'gender', 'date_of_birth']

This is the easiest way to describe an interface. The input document is
human readable even for non coders and quite simple to edit and maintain. It
also keeps declaration and validation in separate files.


Validating data
---------------

Now that we know how our data are supposed to look, we want to validate and
optionally process them. The easiest way to do so are two simple functions
called :py:func:`cutplace.validate` and :py:func:`cutplace.rows`.
Both of them take to parameters: the path to a CID and the path to the data
to validate or read. For example::

    >>> valid_data_path = os.path.join(os.pardir, 'tests', 'data', 'valid_customers.csv')
    >>> cutplace.validate(cid_path, valid_data_path)

If the data are valid, :py:func:`cutplace.validate` seemingly does nothing.
For broken data, it raises :py:exc:`cutplace.error.DataError`.

To also process the data after each row has been validated, use::

    >>> for row in cutplace.rows(cid_path, valid_data_path):
    ...     pass  # We could also do something useful with the data in ``row`` here.

We could easily extend the loop body to process the data in some meaningful
way such as inserting them in a database.

Instead of paths to files, both functions also take a
:py:class:`cutplace.Cid` and / or filelike object ready to read::

    >>> import io
    >>> cid = cutplace.Cid(cid_path)
    >>> with io.open(valid_data_path, 'r', encoding=cid.data_format.encoding, newline='') as data_stream:
    ...     cutplace.validate(cid, data_stream)

If you need more control over the validation or reading process, take a look
at the :py:mod:`cutplace.Reader` class. It provides a simple generator function
:py:func:`cutplace.Reader.rows` that returns all data rows. If you are familiar
with Python's :py:func:`csv.reader`, you already know how to use it.


Dealing with errors
-------------------

So far we only had to deal with valid data.  But what happens if the data do
not conform to the CID? Let's take a look at it::

    >>> import cutplace.errors
    >>> broken_data_path = os.path.join(os.pardir, 'tests', 'data', 'broken_customers.csv')
    >>> cutplace.validate(cid, broken_data_path)
    Traceback (most recent call last):
        ...
    cutplace.errors.FieldValueError: broken_customers.csv (R4C1): cannot accept field 'branch_id': value '12345' must match regular expression: '38\\d\\d\\d'

Apparently the first broken data item causes the validation to stop with an
:py:exc:`cutplace.errors.FieldValueError`, which is a descendant of
:py:exc:`cutplace.errors.CutplaceError`. In many cases this is what you want.

Sometimes however the requirements for an application will state that all
valid data should be processed and invalid data should be put aside for
further examination, for example by writing them to a log file. This is
easy to implement using :py:func:`cutplace.rows` with the optional
parameter ``on_error='yield'``. With this enabled, the generator always
returns a value even for broken rows. The difference however is that broken
rows do not result in a list of values but in a result of type
:py:exc:`cutplace.errors.DataError`. It is up to you to detect this and
process the different kinds of results properly.

Here is an example that prints any data related errors detected during
validation::

    >>> broken_data_path = os.path.join(os.pardir, 'tests', 'data', 'broken_customers.csv')
    >>> for row_or_error in cutplace.rows(cid, broken_data_path, on_error='yield'):
    ...     if isinstance(row_or_error, Exception):
    ...         if isinstance(row_or_error, cutplace.errors.CutplaceError):
    ...             # Print data related error details and move on.
    ...             print(row_or_error)
    ...         else:
    ...             # Let other, more severe errors terminate the validation.
    ...             raise row_or_error
    ...     else:
    ...         pass  # We could also do something useful with the data in ``row`` here.
    broken_customers.csv (R4C1): cannot accept field 'branch_id': value '12345' must match regular expression: '38\\d\\d\\d'
    broken_customers.csv (R5C2): cannot accept field 'customer_id': value must be an integer number: 'XX'
    broken_customers.csv (R6C6): cannot accept field 'date_of_birth': date must match format DD.MM.YYYY (%d.%m.%Y) but is: '30.02.1994' (day is out of range for month)

Note that it is possible for the reader to throw other exceptions, for example
:py:exc:`IOError` in case the file cannot be read at all or :py:exc:`UnicodeError`
in case the encoding does not match. You should not continue after such errors as
they indicate a problem not related to the data but either in the specification
or environment.

The ``on_error`` parameter can also take the values ``'raise'`` (which is the
default and raises a :py:exc:`cutplace.errors.CutplaceError` on encountering the
first error as described above) and ``'continue'``, which silently ignores
any error and moves on with the next row. The latter can be useful during
prototyping a new application when CID's and data are in a constant state of
flux. In production code ``on_error='continue'`` mainly represents a very
efficient way to shoot yourself into the foot.


Processing data
---------------

As a first step, we should figure out where in each row we can find the first
name and the surname. We need to do this only once so this happens outside of
the processing loop. The names used to find the indices must match the names
used in the CID::

    >>> first_name_index = cid.field_index('first_name')
    >>> surname_index =  cid.field_index('surname')

Now we can read the data just like before. Instead of a simple ``pass`` loop
we obtain the first name from ``row`` and check if it starts with ``'J'``. If
so, we compute the full name and print it::

    >>> for row in cutplace.rows(cid, valid_data_path):
    ...   first_name = row[first_name_index]
    ...   if first_name.startswith('J'):
    ...      surname = row[surname_index]
    ...      full_name = surname + ', ' + first_name
    ...      print(full_name)
    Doe, John
    Miller, Jane

Of course nothing prevents you from doing more glamorous things here like
inserting the data into a database or rendering them to a dynamic web page.


Partial validation
------------------

If performance is an issue, validation of field formats and row checks can be
limited to a specified number of rows using the parameter
``validate_until``. Any integer value greater than 0 specifies the
number of rows after which validation should stop. ``None`` means that the
whole input should be validated (the default) while the number ``0``
specifies that no row should be validated.

Functions that support ``validate_until`` are:

* :py:func:`cutplace.validate`
* :py:func:`cutplace.rows`
* :py:func:`cutplace.Reader.__init__`

Pure validation functions such as :py:func:`cutplace.validate` completely
stop processing the input after reaching the limit while reading functions
such as :py:func:`cutplace.rows` keep producing rows - just without
validating them.

A typical use case would be enabling full validation during testing and
reducing validation to the first 100 rows in the production environment.
Ideally this would detect all errors during testing (when performance is less
of an issue) and quickly process the data in production while still detecting
errors early in the data.


Putting it all together
-----------------------

To recapitulate and summarize the previous sections here is a little code
fragment containing a complete example you can use as base for your own
validation code::

    >>> # Validate a test CSV file.
    >>> import os.path
    >>> from cutplace import Cid, Reader
    >>> # Change this to use your own files.
    >>> cid_path = os.path.join(os.pardir, 'tests', 'data', 'cids', 'customers.ods')
    >>> data_path = os.path.join(os.pardir, 'tests', 'data', 'valid_customers.csv')
    >>> # Define the interface.
    >>> cid = Cid(cid_path)
    >>> # Validate the data.
    >>> for row in cutplace.rows(cid, data_path):
    ...   pass # We could also do something useful with the data in ``row`` here.

In case you want to process the data, simply replace the ``pass`` inside the
loop by whatever needs to be done.

In case you want to continue even if a row was rejected, use the optional
parameter ``on_error='yield'`` as described earlier.


.. _writing-data:

Writing data
------------

To validate written data, use :py:class`cutplace.Writer`. A ``Writer`` needs
a CID to validate against and an output to write to. The output can be any
filelike object such as a file or an :py:class:`io.StringIO`. For example::

    >>> import io
    >>> out = io.StringIO()

Now you can create a writer and write a valid row to it::

    >>> writer = cutplace.Writer(cid, out)
    >>> writer.write_row(['38000', '234', 'John', 'Doe', 'male', '08.03.1957'])

Attempting to write broken data results in an :py:exc:`Exception` derived
from :py:exc:`cutplace.errors.CutplaceError`::

    >>> writer.write_row(['38000', 'not a number', 'Jane', 'Miller', 'female', '04.10.1946']) #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    FieldValueError: <io> (R1C2): field 'customer_id' must match format: value must be an integer number: 'not a number'

Note that after a :py:exc:`~.CutplaceError` you can continue writing. For any other
:py:exc:`Exception` such as :py:exc:`IOError` it is recommended to stop writing and
consider it an unrecoverable situation.

Once done, close both the writer and the output::

    >>> writer.close()
    >>> out.close()

As :py:class:`cutplace.Writer` implements the context manager protocol, you
can also use the ``with`` statement to automatically
:py:func:`~cutplace.Writer.close` it when done.

Note that :py:func:`cutplace.Writer.close` performs cutplace checks and
consequently can raise a :py:exc:`cutplace.errors.CheckError`.


Advanced usage
==============

In the previous section, you learned how to read a CID and use it to validate
data using a few simple API calls. You also learned how to handle errors
detected in the data.

With this knowledge, you should be able to write your own small validation
scripts that process the results. For instance, you could add your own code
to log errors, send validation reports via email or automatically insert
accepted rows in a data base. The Python standard library offers powerful
modules for all these tasks.

In case you are already happy and found everything you need, you can stop
reading this chapter and move on with implementing your tasks.

If however you need more flexibility, suffer from API
`OCPD <http://en.wikipedia.org/wiki/Obsessive-compulsive_personality_disorder>`_
or just want to know what else cutplace offers in case you might need it one
day, the following sections describe the lower level hooks of cutplace API.
They are more powerful and flexible, but also more difficult to use.


Building a CID in the code
--------------------------

In some cases it might be preferable to include the CID in the code, for
instance for trivial interfaces that are only used internally. Here is an
example of a simple CID for CSV data with 3 fields:

First, import the necessary modules::

    >>> from cutplace import data
    >>> from cutplace import errors
    >>> from cutplace import fields
    >>> from cutplace import interface

Next create an empty CID::

    >>> cid = Cid()

As the CID will not be read from an input file, error messages would not be
able to refer to any file in case of errors. To have at least some reference,
we need to tell the CID that it is declared from source code::

    >>> cid.set_location_to_caller()

That way, error messages will refer you to the Python module where this call
happened.

Next we can add rows as read from a CID file using
:py:meth:`cutplace.Cid.add_data_format()`,
:py:meth:`cutplace.Cid.add_field_format()` and
:py:meth:`cutplace.Cid.add_check()`::

    >>> # Use CSV as data format. This is the same as having a spreadsheet
    >>> # with the cells:
    >>> #
    >>> # | F | Format         | Delimited |
    >>> # | F | Item separator | ;   |
    >>> cid.add_data_format_row([cutplace.data.KEY_FORMAT, data.FORMAT_DELIMITED])
    >>> cid.add_data_format_row([cutplace.data.KEY_ITEM_DELIMITER, ';'])
    >>>
    >>> # Add a couple of fields.
    >>> cid.add_field_format(['id', '', '', '1...5', 'Integer'])
    >>> cid.add_field_format(['name'])
    >>> cid.add_field_format(['date_of_birth', '', 'X', '', 'DateTime', 'YYYY-MM-DD'])
    >>>
    >>> # Make sure that the ``id`` field contains only unique values.
    >>> cid.add_check(['id_must_be_unique', 'IsUnique', 'id'])
    >>> cid.field_names
    ['id', 'name', 'date_of_birth']

If any of this methods cannot handle the parameters you passed, they raise a
:py:exc:`cutplace.errors.CutplaceError` with a message describing what went wrong.
For example::

    >>> cid.add_check([]) #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    InterfaceError: <source> (R1C2): check row (marked with 'c') must contain at least 2 columns


Adding your own field formats
-----------------------------

Cutplace already ships with several field formats found in
:py:mod:`cutplace.fields` module that should cover most needs. If
however you have some very special requirements, you can write your own
formats.

Simply inherit from :py:class:`cutplace.fields.AbstractFieldFormat` and
optionally provide a constructor to parse the ``rule`` parameter. Next,
implement :py:meth:`~cutplace.fields.AbstractFieldFormat.validated_value()`
which validates that the text in ``value`` conforms to ``rule``. If not,
raise a :py:exc:`FieldValueError` with a descriptive error message.

Here is a very simple example of a field format that accepts values of "red",
"green" and "blue"::

    >>> class ColorFieldFormat(fields.AbstractFieldFormat):
    ...     def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
    ...         super(ColorFieldFormat, self).__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value='')
    ...
    ...     def validated_value(self, value):
    ...         # Validate that ``value`` is a color and return it.
    ...         assert value
    ...         if value not in ['red', 'green', 'blue']:
    ...             raise errors.FieldValueError('color value is %r but must be one of: red, green, blue' % value)
    ...         return value
    >>> color_field = ColorFieldFormat('roof_color', False, '', '', cid.data_format)
    >>> color_field.validated('red')
    'red'

The ``value`` parameter is a string. Cutplace ensures that
:py:meth:`~cutplace.fields.AbstractFieldFormat.validated_value()` will never
be called with an empty ``value`` parameter, hence the ``assert value`` - it
will cause an :py:exc:`AssertionError` if ``value`` is ``''`` or ``None``
because that would mean that the caller is broken.

Of course you could have achieved similar results using
:py:class:`~cutplace.fields.ChoiceFieldFormat`. However, a custom field
format can do more. In particular,
:py:meth:`~cutplace.fields.AbstractFieldFormat.validated_value()` does not
have to return a string. It can return any Python type and even ``None``.

Here's a more advanced :py:class`ColorFieldFormat` that returns the color as
a tuple of RGB values between 0 and 1::

    >>> class ColorFieldFormat(fields.AbstractFieldFormat):
    ...     def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
    ...         super(ColorFieldFormat, self).__init__(field_name, is_allowed_to_be_empty, length, rule, data_format, empty_value='')
    ...
    ...     def validated_value(self, color_name):
    ...         # Validate that ``color_name`` is a color and return its RGB representation.
    ...         assert color_name
    ...         if color_name == 'red':
    ...             result = (1.0, 0.0, 0.0)
    ...         elif color_name == 'green':
    ...             result = (0.0, 1.0, 0.0)
    ...         elif color_name == 'blue':
    ...             result = (0.0, 1.0, 0.0)
    ...         else:
    ...             raise errors.FieldValueError('color name is %r but must be one of: red, green, blue' % color_name)
    ...         return result

For a simple test, let's see this field format in action::

    >>> color_field = ColorFieldFormat('roof_color', False, '', '', cid.data_format)
    >>> color_field.validated('red')
    (1.0, 0.0, 0.0)
    >>> color_field.validated('yellow')
    Traceback (most recent call last):
    ...
    cutplace.errors.FieldValueError: color name is 'yellow' but must be one of: red, green, blue

Before you learned that
:py:meth:`~cutplace.fields.AbstractFieldFormat.validated_value()`
never gets called with an empty value. So what happens if you declare a color
field that allows empty values? For example::

    >>> # Sets ``is_allowed_to_be_empty`` to ``True`` to accept empty values.
    >>> color_field = ColorFieldFormat('roof_color', True, '', '', cid.data_format)
    >>> color_field.validated('')
    ''
    >>> # Not quiet a color tuple...

Well, that's not quite what we want. Instead of an empty string, a reasonable
default RGB tuple would be a lot more useful. Say, ``(0.0, 0.0, 0.0)`` to
represent black.

Fortunately field formats can just specify that by using the ``empty_value``
parameter in the constructor. When passed to the ``super`` constructor in
:py:class:`~cutplace.fields.AbstractFieldFormat`, everything will be taken
care of. So here's a slightly modified version::

    >>> class ColorFieldFormat(fields.AbstractFieldFormat):
    ...     def __init__(self, field_name, is_allowed_to_be_empty, length, rule, data_format):
    ...         super(ColorFieldFormat, self).__init__(field_name, is_allowed_to_be_empty, length, rule, data_format,
    ...                 empty_value=(0.0, 0.0, 0.0)) # Use black as "empty" color.
    ...
    ...     def validated_value(self, color_name):
    ...         # (Exactly same as before)
    ...         assert color_name
    ...         if color_name == 'red':
    ...             result = (1.0, 0.0, 0.0)
    ...         elif color_name == 'green':
    ...             result = (0.0, 1.0, 0.0)
    ...         elif color_name == 'blue':
    ...             result = (0.0, 1.0, 0.0)
    ...         else:
    ...             raise cutplace.errors.FieldValueError('color name is %r but must be one of: red, green, blue' % color_name)
    ...         return result

Let's give it a try::

    >>> color_field = ColorFieldFormat('roof_color', True, '', '', cid.data_format)
    >>> color_field.validated('red')
    (1.0, 0.0, 0.0)
    >>> color_field.validated('')
    (0.0, 0.0, 0.0)


Adding your own checks
----------------------

Writing checks is quite similar to writing field formats. However, the
interaction with the validation is more complex.

Checks have to implement certain methods described in
:py:class:`cutplace.checks.AbstractCheck`. For each check, cutplace performs
the following actions:

#. When reading the CID, call the check's :py:meth:`__init__()`.
#. When starting to read a set of data, call the checks's :py:meth:`reset()`.
#. For each row of data, call the checks's :py:meth:``check_row()``.
#. When done with a set of data, call the checks's :py:meth:`check_at_end()`.

The remainder of this section describes how to implement each of
these methods.

As an example, we implement a check to ensure that each customer's full name
requires less than 100 characters. The field formats already ensure that
``first_name`` and ``last_name`` are at most 60 characters each. However,
assuming the full name is derived using the expression::

    last_name + ', ' + first_name

this could lead to full names with up to 122 characters.

To implements this check, start by inheriting from
:py:class:`cutplace.checks.AbstractCheck`::

    >>> from cutplace import checks
    >>> class FullNameLengthIsInRangeCheck(checks.AbstractCheck):
    ...     """Check that total length of customer name is within the specified range."""

Next, implement a constructor to which cutplace can pass the values
found in the CID. For example, for our check the CID would contain:

+-+-------------------------------------------+------------------------+-------+
+ +Description                                +Type                    +Rule   +
+=+===========================================+========================+=======+
+C+full name must have at most 100 characters +FullNameLengthIsInRange +...100 +
+-+-------------------------------------------+------------------------+-------+

When cutplace encounters this line, it will create a new check by calling
:py:meth:`FullNameLengthIsInRangeCheck.__init__()`, passing the following
parameters:

* ``description='customer must be unique'``, which is just a human readable
  description of the check to refer to it in error messages
* ``rule='...100'``, which describes what exactly the check
  should do. Each check can define its own syntax for the rule. In case of
  :py:class:`FullNameLengthIsInRange` the rule describes a
  :py:class:`cutplace.ranges.Range`.
* ``available_field_names=['branch_id', 'customer_id', 'first_name',
  'last_name', 'gender', 'date_of_birth']`` (as defined in the CID and using
  the same order)
* ``location`` being the :py:class:`cutplace.errors.Location` in the CID
  where the check was defined.

The constructor basically has to do 3 things:

#. Call the super constructor
#. Perform optional initialization needed by the check that needs to be
   done only once and not on each new data set. In most cases, this involves
   parsing the ``rule`` parameter and obtain whatever information the
   checks needs from it.
#. Call ``self.reset()``. This is not really necessary for this check, but in most
   cases it will make your life easier because you can avoid redundant initializations
   in the constructor.

To sum it up as code::

    >>> from cutplace import ranges
    >>> class FullNameLengthIsInRangeCheck(checks.AbstractCheck):
    ...     """Check that total length of customer name is within the specified range."""
    ...     def __init__(self, description, rule, available_field_names, location=None):
    ...         super(FullNameLengthIsInRangeCheck, self).__init__(description, rule, available_field_names, location)
    ...         self._full_name_range = ranges.Range(rule)
    ...         self.reset()

Once cutplace is done reading the CID, it moves on to data. For each set of
data it calls the checks' :py:meth:`~cutplace.checks.AbstractCheck.reset()`
method. For our simple check, no actions are needed so we are good because
:py:meth:`~cutplace.checks.AbstractCheck.reset()` already does nothing.

When cutplace validates data, it reads them row by row. For each row, it
calls :py:meth:`~cutplace.fields.AbstractFieldFormat.validated()` on each
cell in the row. In case all cells are valid, it collects them in a
dictionary which maps the field name to its native value. Recall the interface
from the :doc:`tutorial`, which defined the following fields:

+-+--------------------+----------+------+------+--------+------------+
+ +Name                +Example   +Empty?+Length+Type    +Rule        +
+=+====================+==========+======+======+========+============+
+F+branch_id           +38000     +      +5     +        +            +
+-+--------------------+----------+------+------+--------+------------+
+F+customer_id         +16        +      +2...  +Integer +10:65535    +
+-+--------------------+----------+------+------+--------+------------+
+F+first_name          +Jane      +      +...60 +        +            +
+-+--------------------+----------+------+------+--------+------------+
+F+surname             +Doe       +      +...60 +        +            +
+-+--------------------+----------+------+------+--------+------------+
+F+gender              +female    +      +2...6 +Choice  +male, female+
+-+--------------------+----------+------+------+--------+------------+
+F+date_of_birth       +27.02.1946+X     +10    +DateTime+DD.MM.YYYY  +
+-+--------------------+----------+------+------+--------+------------+

Now consider a data row with the following values:

+---------+-----------+----------+-------+------+-------------+
+Branch id+Customer id+First name+Surname+Gender+Date of birth+
+=========+===========+==========+=======+======+=============+
+38111    +96         +Andrew    +Dixon  +male  +02.10.1913   +
+---------+-----------+----------+-------+------+-------------+

The row map for this row would be::

  row_map = {
      'branch_id': 38111,
      'customer_id': 96,
      'first_name': 'Andrew',
      'last_name': 'Dixon',
      'gender': 'male',
      'date_of_birth': time.struct_time(tm_year=1913, tm_mon=10, tm_mday=2, ...)
  }

With this knowledge, we can easily implement a :py:meth:`check_row()` that
computes the full name and checks that it is within the required range. If
not, it raises a :py:exc:`~cutplace.errors.CheckError`::

    >>> def check_row(self, row_map, location):
    ...     first_name = row_map['first_name']
    ...     surname = row_map['surname']
    ...     full_name = surname + ', ' + first_name
    ...     full_name_length = len(full_name)
    ...     try:
    ...         self._full_name_range.validate('full name', full_name_length)
    ...     except cutplace.RangeValueError as error:
    ...         raise cutplace.errors.CheckError('full name length is %d but must be in range %s: %r' \
    ...                 % (full_name_length, self._full_name_range, full_name))

And finally, there is :py:meth:`cutplace.checks.AbstractCheck.check_at_end()`
which is called when all data rows have been processed. Note that
:py:meth:`check_at_end()` does not have any parameters that contain actual
data. Instead you typically would collect all information needed by
:py:meth:`check_at_end()` in :py:meth:`check_row()` and store them in
instance variables. For an example, take a look at the source code of
:py:class:`cutplace.checks.IsUniqueCheck`.

Because our :py:class:`FullNameLengthIsInRangeCheck` does not need to do
anything here, we can omit it and keep inherit an empty implementation from
:py:meth:`cutplace.checks.AbstractCheck.check_at_end()`.


.. _using-own-check-and-field-formats:

Using your own checks and field formats
---------------------------------------

Now that you know how to write our own checks and field formats, it would be
nice to actually utilize them in a CID. For this purpose, cutplace lets you
import plugins that can define their own checks and field formats.

Plugins are standard Python modules that define classes based on
:py:class:`cutplace.fields.AbstractCheck` and
:py:class:`cutplace.fields.AbstractFieldFormat`. For our example, create a
folder named :file:`~/cutplace_plugins` and store a Python module named
:file:`myplugins.py` in it with the following contents::

.. literalinclude:: ../examples/plugins.py


The CID can now refer to :py:class:`ColorFieldFormat` as ``Color`` (without
``FieldFormat``) and to :py:class:`FullNameLengthIsInRangeCheck` as
``FullNameLengthIsInRange`` (without ``Check``). For example:

+-+-----------------+-------+------+------+-----+----+
+ +Interface: colors+       +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+ +                 +       +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+ +Data format      +       +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+D+Format           +CSV    +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+D+Header           +1      +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+ +                 +       +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+ +Fields           +       +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+ +Name             +Example+Empty?+Length+Type +Rule+
+-+-----------------+-------+------+------+-----+----+
+F+item             +tree   +      +      +     +    +
+-+-----------------+-------+------+------+-----+----+
+F+color            +green  +      +      +Color+    +
+-+-----------------+-------+------+------+-----+----+

See: :download:`cid_colors.ods <../examples/cid_colors.ods>`

Here is a data file where all but one row conforms to the CID:

.. literalinclude:: ../examples/colors.csv

See: :download:`colors.csv <../examples/colors.csv>`

To tell cutplace where the plugins folder is located, use the command line
option :option:`--plugins`. Assuming that your :file:`myplugins.py` is stored in
:file:`~/cutplace_plugins` you can run::

  cutplace --plugins ~/cutplace_plugins cid_colors.ods colors.csv

The output is::

  ERROR:cutplace:field error: colors.csv (R5C2): field 'color' must match format: color name is 'yellow' but must be one of: red, green, blue
  colors.csv: rejected 1 of 5 rows. 0 final checks failed.

If you are unsure which plugins exactly cutplace imports, use
:option:`--log=info`. For example, the output could contain::

  INFO:cutplace:import plugins from "/Users/me/cutplace_plugins"
  INFO:cutplace:  import plugins from "/Users/me/cutplace_plugins/myplugins.py"
  INFO:cutplace:    fields found: ['ColorFieldFormat']
  INFO:cutplace:    checks found: ['FullNameLengthIsInRangeCheck']

