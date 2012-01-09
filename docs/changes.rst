================
Revision history
================

This chapter describes improvements compared to earlier versions of cutplace.

Version 0.7.0, 2012-01-09
=========================

* Added command line option ``--plugins`` to specify a folder where cutplace
  looks for plugins declaring additional field formats and checks. For
  details, see :ref:`using-own-check-and-field-formats`.

* Changed ``interface.validatedRows(..., errors="yield")`` to yield
  ``tools.ErrorInfo`` in case of error instead of ``Exception``.

* Reduced memory foot print of CSV reading (Ticket #32). As a side effect,
  all formats now read and validate in separate threads, which should
  result in a slight performance improvement on systems with multiple CPU
  cores.

* Cleaned up developer reports (Ticket #40). Most of the reports are now
  built using Jenkins as described in :ref:`jenkins`, the only exception
  being the profiler report to monitor performance. Also changed build
  instructions to favor ``ant`` over ``setup.py``.

* Cleaned up API:

  * cutplace and cutsniff have a similar ``main()`` that returns an
    integer exit code without actually calling ``sys.exit()``.

* Cleaned up formatting to conform to PEP8 style.

Version 0.6.8, 2011-07-26
=========================

* Fixed "see also" location in error messages caused by ``IsUniqueCheck``
  which used the current location as original location.

* Fixed ``AttributeError`` when using the API method
  ``AbstractFieldFormat.getFieldValueFor()``.

* Fixed ``ImportError`` during installation on systems lacking the Python
  profiler.

Version 0.6.7, 2011-05-24
=========================

* Added option ``--names`` to :ref:`cutsniff` to specify field names as comma
  separated list of names. Without this option, the names found in the last
  row specified by ``--head`` are used. Without this option, fields names will
  have generated values the user manually will have to change in order to get
  meaningful names.

Version 0.6.6, 2011-05-18
=========================

* Cleaned up debugging output.

Version 0.6.5, 2011-05-17
=========================

* Added command line option ``--header`` to :ref:`cutsniff` to exclude header
  rows from analysis.

* Fixed build error in case module coverage was not installed by making
  coverage a required module again.

Version 0.6.4, 2011-03-19
=========================

* Added :ref:`cutsniff`, a tool to create an ICD by analyzing an existing data
  file.

* #21: Fixed automatic detection of Excel format when reading ICDs using the
  web interface. (Tickte #21).

* Fixed ``AttributeError`` when data format was set to "delimited".

Version 0.6.3, 2010-10-25
=========================

* Fixed ``InterfaceControlDocument.checkNames`` which actually contained the
  field names. Additionally, checkNames now contains the names in the order
  they were declared in the ICD. Consequently the checks are performed in this
  order during validation unlike until now, where the internal hashcode
  decided the order of checks. (Ticket #35)

* Improved documentation, in particular:

  * Added more information on writing field format and checks of your own. It
    still lacks details on how to actually use these in an ICD though.
    (Ticket #33)

  * Cleaned up introductions of most chapters with the intention to make them
    easier to comprehend.

* Changed public instance variables to properties. This allows to mark many of
  them as read only, and also makes them show up in the API reference.
  (Ticket #34).

Version 0.6.2, 2010-09-29
=========================

* Added input location for error messages caused by failed checks.
  (Ticket #26, #27 and #28)

* Added error message if a field name is a Python keyword such as
  ``class`` or ``if``. This avoids strange error messages if later an
  ``IsUnique`` check refers to such a field. (Ticket #20)

* Changed style for error messages referring to locations in CSV, ODS
  and Excel data to R1C1. For example, "R17C23" points to row 15,
  column 23.

* Changed internal modules to use "_" as prefix in name. This removes them
  from the API documentation. Furthermore, module ``tools`` has been split into
  public ``tools`` and internal ``_tools``.

* Changed interface for listeners of validation events:

  * Renamed `ValidationListener` to `BaseValidationListener`.

  * Added parameter `location` to `acceptedRow()` which is of type
    `tools.InputLocation`.

* Cleaned up API documentation, using reStructured Text as output format
  and adding a tutorial in chapter :doc:`api`.

* Cleaned up logging to slightly improve performance.


Version 0.6.1, 2010-04-25
=========================

* Added data format properties "decimal delimiter" (default: ".") and
  "thousands delimiter" (default: none). Fields of type `Decimal` take them
  into account. See also: Ticket #24.

* Added detailed error locations to some errors detected when reading the
  ICD.

* Changed choice fields to be case sensitive.

* Changed choice fields to support values in quotes. That way it is also
  possible to use escape sequences within values. Values with non ASCII
  characters (such as umlauts) have to be quotes now. See also: Ticket #25.

* Renamed module `cutplace.range` to `cutplace.ranges` to avoid name clash
  with the built in Python function `range()`. In case you have an older
  version of cutplace installed and plan to import the cutplace Python
  module using::

    from cutplace import * # ugly, avoid anyway

  you will have to manually remove the files :file:`cutplace/range.py`
  and :file:`cutplace/range.pyc` (in case it exists).

* Added API documentation available from
  <http://cutplace.sourceforge.net/api/>.

Version 0.6.0, 2010-03-29
=========================

* Changed license from GPL to LGPL so closed source application can import
  the cutplace Python module.

* Fixed validation of empty dates with DateTime fields.

* Added support for letters, hex numbers and symbolic names in ranges.

* Added support for letters, escaped characters, hex numbers and symbolic
  names in item delimiters for data formats.

* Added auto detection of item delimiters tab ("\\t", ASCII 9) and vertical
  bar (|). [Josef Wolte]

* Cleaned up code for field validation.


Version 0.5.8, 2009-10-12
=========================

* Changed Unicode encoding errors to result in the row to be rejected similar
  to a row with an invalid field instead of a simple message in the console.

* Changed command line exit code to 1 instead of 0 in case validation errors
  were found in any data file specified.

* Changed command line exit code to 4 instead of 0 for errors that could not
  be handled or reported otherwise (usually hinting at a bug in the code).
  This case also results in a stack trace to be printed.


Version 0.5.7, 2009-09-07
=========================

* Fixed validation of empty Choice fields that according to the ICD were
  allowed to be empty but nevertheless were rejected.

* Fixed a strange error when run using Jython 2.5.0 on certain platforms.
  The exact message was: ``TypeError: 'type' object is not iterable``.

Version 0.5.6, 2009-08-19
=========================

* Added a short summary at the end of validation. Depending on the result,
  this can be either for instance ``eggs.csv: accepted 123 rows`` or
  ``eggs.csv: rejected 7 of 123 rows. 2 final checks failed.``.

* Changed default for ``--log`` from``info`` to ``warning``.

* Improved confusing error message when a field value is rejected because
  of improper length.

* Fixed ``ImportError`` when run using Jython 2.5, which does not support the
  Python standard module ``webbrowser``. Attempting to use ``--browser`` will
  result in an error message nevertheless.

Version 0.5.5, 2009-07-26
=========================

* Added summary to validation results shown by web interface.

* Fixed validation of Excel data using the web interface.

* Cleaned up reporting of errors not related to validation via web interface.
  The resulting web page now is less cluttered and the HTTP result is a
  consistent 40x error.

Version 0.5.4, 2009-07-21
=========================

* Fixed ``--split`` which did not actually write any files. (Ticket #19)

* Fixed encoding error when reading data from Excel files that used cell
  formats of type data, error or time.

* Fixed validation of Decimal fields, which resulted in a
  ``NotImplementedError``.

* Fixed internal handling of ranges with a default, which resulted in a
  ``NameError``.

Version 0.5.3, 2009-07-18
=========================

* Added command line option ``--split`` to store accepted and rejected data in two
  separated files. See also: ticket #17.

* Fixed handling of non ASCII data, which did not work properly with all
  formats. Now cutplace consistently uses Unicode strings to internally
  represent data items. See also: ticket #18.

* Improved error messages and removed stack trace in cases where it does not
  add anything of value such as for I/O errors.

* Changed development status from alpha to beta.

Version 0.5.2, 2009-06-11
=========================

* Fixed missing setup script.

Version 0.5.1, 2009-06-11
=========================

* Added support for ICDs in Excel and ODS format for built in web server.

* Changed representation of integer number read from Excel data: instead
  of for example "123.0" this now renders as "123".

* Improved memory usage for data and ICDs in ODS format.

* Fixed reading of ICDs in Excel and ODS format.

* Fixed TypeError when the CSV delimiters specified in the ICD were encoded
  in Unicode.

Version 0.5.0, 2009-06-02
=========================

* Fixed handling of Excel numbers, dates and times. Refer to the
  section on Excel data format for details.

* Changed order for field format (again): It now is
  name/example/empty/length/type/rule instead of
  name/example/empty/type/length/rule.

* Changed optional items for field format: now the field name is the
  only thing required.  If no type is specified, "Text" is used.

* Added a proper tutorial that starts with a very simple ICD and
  improves it step by step. The old tutorial presented one huge ICD
  and attempted to explain everything in it, which could easily
  overwhelm the reader.

* Migrated documentation from DocBook to RestructuredText.

* Improved build and installation process (``setup.py``).

Version 0.4.4, 2009-05-23
=========================

* Fixed checks when validating more than one data file from the command line.
  Until now the checks did preserve internal state information needed to
  perform the check. For instance, IsUnique check remembered the keys of all
  rows read so far. So when a data file contained a row with a key that already
  showed up in an earlier data file, the check failed. To prevent this from
  happening, ``validate()`` now resets all checks. See also: Ticket #9.

* Fixed detection of characters outside of the "Allowed characters" range.
  Apparently this never worked until now.

* Fixed handling of empty choices consisting only of white space.

* Fixed detection of fixed fields without length.

* Fixed handling of white space in field items of fixed length data.

* Added plenty of test cases and consequently performed a couple of minor
  fixes, improvements and clean ups.

Version 0.4.3, 2009-05-18
=========================

* Fixed auto detection of delimiters in a CSV file, which got broken when
  switching to Python's built in CSV reader with version 0.3.1. See also:
  Ticket #8.

Version 0.4.2, 2009-05-17
=========================

* Added validation for data format property "Allowed characters", which can be
  used with all data formats.

* Added data format property "Header" to specify the number of header rows that
  should be skipped without validation. This property can be used with all data
  formats.

* Added data format property "Sheet" to specify the number of the sheet to
  validate in spreadsheet data formats (Excel and ODS).

* Added complex ranges that consist of several sub ranges separated by a comma
  (,). For example: "10:20, 30:40" means that a value must be between 10 and 20
  or 30 and 40.

* Moved forums to http://apps.sourceforge.net/phpbb/cutplace/.

* Moved project site and issue tracker to
  http://apps.sourceforge.net/trac/cutplace/.

* Fixed handling of data rows with too few or too many items.

* Cleaned up error handling and error messages.

Version 0.4.1, 2009-05-10
=========================

* Added support for Excel and ODS data formats.

Version 0.4.0, 2009-05-06
=========================

* Added support for ICDs stored in Excel format. In order for this to work, the
  xlrd Python package needs to be installed. It is available from
  http://pypi.python.org/pypi/xlrd.

* Changed ICD format: Inserted a new column after the field name and before the
  field type that can contain an optional example value. This enables readers
  to quickly grasp the meaning of a field by taking a glimpse at the first few
  columns instead of having to "decipher" the field type and rule.

Version 0.3.1, 2009-05-03
=========================

* Added proper error messages for several possible error the user might make
  when writing an ICD. So far these errors resulted into confusing messages
  about failed assertions, attempted ``NoneType`` accesses and the like.

* Added requirement that field names in the ICD only use ASCII letters, digits
  and underscore (_). This is necessary to prevent Python errors in checks that
  refer to field values using Python variables, such as DistinctCount and
  IsUnique.

* Changed CSV parser to use Python's built in one. This works around the
  following issues:

  - Improved performance when working with CSV data (about 4 times faster).

  - Error when reading valid CSV data that contained nothing but a single item
    separator.

  However, it also introduces new issues:

  - Increased memory usage when working with CSV data because ``csv.reader``
    does not fit well with the ``AbstractParser`` class. Currently the whole
    file is read into memory.

  - Lack of any error detection in the CSV structure. For example, unclosed
    quotes at the end or inconsistent line feeds do not raise any errors.

* On the long run, cutplace will need its own CSV parser. If only this would
  not be so boring to code...

* Improved error messages for broken field names and types in the ICD.

Version 0.3.0, 2009-04-28
=========================

* Fixed error messages in case field name or type was missing in ICD.

* Fixed handling of percent sign (%) in ``DateTime`` field format.

* Changed syntax to specify ranges like field lengths or rules for ``Integer``
  fields formats. Use ":" instead of "...".

  There are basically two reasons for this change: Firstly, this looks more
  Python-like and thus more consistent with other parts of the ICD like the
  "Checks" section which also uses Python syntax in various places. Secondly,
  this avoids issues with Excel which under certain circumstances changes the 3
  characters in "..." to a single character ellipsis. Using ":" still is not
  without issues though: if you use a spreadsheet application to author ICDs,
  most of them think of a value like "1:60" (which could for example specify a
  field length between 1 and 60 characters) to refer to a time of 1 hour and 60
  minutes. To avoid any confusion, disable the cell format auto detection of
  the spreadsheet application by changing all cells to contain "Text".

Version 0.2.2, 2009-04-07
=========================

* Added support to use data encodings other than ASCII by specifying them in
  the data format section of the ICD using the encoding property.

* Added support for fixed data format.

* Added command line option ``--browse`` to be used together with ``--web`` in
  order to open the validation page in the web browser.

* Added command line option ``--icd-encoding`` to specify the character encoding
  to be used with ICDs in CSV format.

Version 0.2.1, 2009-03-29
=========================

* Added support for ICDs in ODS format for command line client.

* Added ``cutplace.exe`` for Windows, which will be generated during
  installation.

* Added automatic installation of setuptools when you try to build cutplace
  using the Subversion repository. This feature is provided by ``ez_setup.py``,
  which is available from the setuptools site.

* Fixed cutplace script, which did exit with an ``ExitQuietlyOptionError`` for
  options that just showed some information and exited (such as ``--help``).

Version 0.2.0, 2009-03-27
=========================

* Added option ``--web`` and ``--port`` to launch web server providing a simple
  graphical user interface for validation.

* Changed ``--listencodings`` to ``--list-encodings``.

Version 0.1.2, 2009-03-22
=========================

* Added ``DistinctCount`` check.

* Added ``IsUnique`` check.

* Added command line option ``--trace``.

* Added support to validate an ICD when no data are specified in the command
  line.

* Cleaned up error messages.

Version 0.1.1, 2009-03-17
=========================

* Initial release.
