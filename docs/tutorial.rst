.. _tutorial:

========
Tutorial
========

This chapter gives a gentle introduction and overview to cutplace. It
introduces a simple set of example data and shows how to write a simple
interface control document (ICD) for it which can be used to validate
the data. Starting from there, the ICD gets refined and improved to
allow more rigorous validations which detect increasingly subtle errors
in the data.

You can find the files for the examples in the ``examples`` folder of
the cutplace source distribution. For your convenience they are also
provided as links at the bottom of each data or ICD file.

A simple set of customer data
=============================

In order to make use of cutplace, you need some data. For this tutorial,
we will use a simple set of customer data:

.. literalinclude:: ../examples/customers.csv

See: :download:`customers.csv <../examples/customers.csv>`

Because this is hard to read here is how the file looks if you
open it in a spreadsheet application such as Excel or Calc:

+---------+-----------+----------+-------+------+-------------+
+Branch id+Customer id+First name+Surname+Gender+Date of birth+
+=========+===========+==========+=======+======+=============+
+38000    +16         +Daisy     +Mason  +female+27.02.1946   +
+---------+-----------+----------+-------+------+-------------+
+38000    +42         +Wendy     +Davis  +female+30.12.1971   +
+---------+-----------+----------+-------+------+-------------+
+38000    +57         +Keith     +Parker +male  +02.06.1984   +
+---------+-----------+----------+-------+------+-------------+
+38000    +76         +Kenneth   +Tucker +male  +15.11.1908   +
+---------+-----------+----------+-------+------+-------------+
+38053    +11         +Carlos    +Barrett+male  +09.02.1929   +
+---------+-----------+----------+-------+------+-------------+
+38053    +20         +Terrance  +Hart   +male  +11.03.1961   +
+---------+-----------+----------+-------+------+-------------+
+38053    +34         +Lori      +Dunn   +female+26.09.1996   +
+---------+-----------+----------+-------+------+-------------+
+38053    +73         +Mary      +Sutton +female+09.12.1982   +
+---------+-----------+----------+-------+------+-------------+
+38053    +83         +Lorraine  +Castro +female+15.08.1978   +
+---------+-----------+----------+-------+------+-------------+
+38111    +31         +Esther    +Newman +female+23.03.1932   +
+---------+-----------+----------+-------+------+-------------+
+38111    +79         +Tyler     +Rose   +male  +17.12.1920   +
+---------+-----------+----------+-------+------+-------------+
+38111    +127        +Andrew    +Dixon  +male  +02.10.1913   +
+---------+-----------+----------+-------+------+-------------+

Describing data format and and field names
==========================================

Now let's try to describe the format of this file. From our initial
pondering we already know the following facts:

#. The data are provided as comma separated values (CSV).
#. The fields in the data have a meaning we can assign a heading to.

Without much further ado, here's how you can tell these facts to cutplace:

+-+-------------------+---+
+ +Interface: customer+   +
+-+-------------------+---+
+ +                   +   +
+-+-------------------+---+
+ +**Data format**    +   +
+-+-------------------+---+
+D+Format             +CSV+
+-+-------------------+---+
+D+Header             +1  +
+-+-------------------+---+
+ +                   +   +
+-+-------------------+---+
+ +**Fields**         +   +
+-+-------------------+---+
+F+branch_id          +   +
+-+-------------------+---+
+F+customer_id        +   +
+-+-------------------+---+
+F+first_name         +   +
+-+-------------------+---+
+F+surname            +   +
+-+-------------------+---+
+F+gender             +   +
+-+-------------------+---+
+F+date_of_birth      +   +
+-+-------------------+---+

See: :download:`icd_customers_field_names_only.csv <../examples/icd_customers_field_names_only.csv>`
or :download:`icd_customers_field_names_only.ods <../examples/icd_customers_field_names_only.ods>`

Let's take a closer look at this.

Row 1 is a heading that simply describes what the document is about: the
interface for customer data.

Row 3 is a section heading to point out that the description of the data
format is about to follow.

Row 4 describes the data format by stating that the ``Format`` is ``CSV``. Did
you notice the ``D`` in the first column? This is a hint for cutplace that the
row contains information about the data format it should be able to process.

Row 5 adds another detail to the data format: data files have a header row
that does not contain data yet. In this case there is only one such row. If
there would no header at all, you could have omitted this row.

Row 7 again is a section heading, this time pointing out that
descriptions about the field formats are about to follow.

The remaining rows then describe the fields that data files must have.
So far we only describe the name of the field, for example
``customer_id``.

.. note::
  A field name must contain only ASCII letters, numbers and underscore
  (_). So blanks, foreign characters such as umlauts and
  punctuation marks are not allowed and will result in an error message
  when cutplace attempts to read the ICD.

  Some examples for valid field names:

  * ``customer_id``

  * ``iso_5218_gender``

  * ``CustomerId``

  For comparison, here are a few broken field names

  * ``customer-id`` - error: contains the punctuation mark "``-``";
    use "``_``" instead.

  * ``customer id``  - error: contains a blank; use "``_``" instead.

  * ``123easy`` - error: starts with a numeric digit; use a letter as
    first character.

Using comments
==============

As already pointed out, if a row in the ICD starts with an empty column,
cutplace skips it without processing in any way. Actually, this would
mean the same for cutplace:

+-+-------------------+---+
+D+Format             +CSV+
+-+-------------------+---+
+D+Header             +1  +
+-+-------------------+---+
+F+branch_id          +   +
+-+-------------------+---+
+F+customer_id        +   +
+-+-------------------+---+
+F+first_name         +   +
+-+-------------------+---+
+F+surname            +   +
+-+-------------------+---+
+F+gender             +   +
+-+-------------------+---+
+F+date_of_birth      +   +
+-+-------------------+---+

But it's a lot harder to read for you, isn't it?

How and where to store the ICD
==============================

So how do you store this information? Cutplace is quite flexible here.
The easiest way would be to use a spreadsheet application such as Excel
or OpenOffice.org's Calc and store it as ``*.xls`` or ``*.ods`` file.
Alternatively you can use the text editor or your choice and store it as
``*.csv``, where columns are separated with a comma (,) and data items
with blanks or commas are embedded between double quotes (").

Concerning the location on your disk, cutplace does not impose any
requirements on you

.. TODO: Recommendations how to name the ICD files.

For this tutorial, we assume both the data and ICD files are stored in
the same folder which and that your current console terminal session already
changed to this folder (using for example the command ``cd``).

Running cutplace for the first time
===================================

Now that we have both a data file and an ICD file, we can finally take a look
at how cutplace actually works.

Open a terminal and change into the folder where where the example data
and ICD files are located::

  cd .../where/ever/examples

Next let's try if cutplace has been installed properly::

  cutplace --version

This should result in an output similar to::

  cutplace.py 0.x.x (2010-xx-xx, rxxx)
  Python 2.5.5, Mac OS 10.5.8 (i386)

The actual version numbers may vary. If your version of cutplace is older then
|release|, consider upgrading to avoid compatibility issues with this
tutorial.

If instead this results in an error message, refer to the chapter on
:doc:`installation` about how to setup cutplace.

In case everything worked out so far, let's finally do what we came here
for: validate that our data conform to the interface we just described::

  cutplace icd_customers_1.ods customers_1.csv

This assumes you used Calc to create the ICD. Users of Excel should
replace the "``.ods``" with "``.xls``", users of text editors with
"``.csv``" respectively.

Summary so far
==============

Let's recap what we learned so far:

* You can use cutplace to validate that data conform to an ICD.

* The ICD is a file you can create with Calc, Excel or your favorite
  text editor.

* As a minimum, the ICD has to specify the data format and the name of
  the fields.

* Rows describing the data format have to start with "``D``".

* Rows describing a field have to start with "``F``".

* Rows starting with an empty column will not be parsed by cutplace and
  can contain any information that is helpful for human readers to
  better understand the interface.

Adding examples
===============

Most people find it easiest to get a general grasp of something by
looking at an example. Cutplace supports this line of thinking by
letting you add an examples for a field right after the name:

+-+--------------------+--------------+
+ +Fields              +              +
+-+--------------------+--------------+
+ +*Name*              +*Example*     +
+-+--------------------+--------------+
+F+branch_id           +**38000**     +
+-+--------------------+--------------+
+F+customer_id         +**16**        +
+-+--------------------+--------------+
+F+first_name          +**Jane**      +
+-+--------------------+--------------+
+F+surname             +**Doe**       +
+-+--------------------+--------------+
+F+gender              +**female**    +
+-+--------------------+--------------+
+F+date_of_birth       +**27.02.1946**+
+-+--------------------+--------------+

See: :download:`icd_customers_with_examples.csv <../examples/icd_customers_with_examples.csv>`
or :download:`icd_customers_with_examples.ods <../examples/icd_customers_with_examples.ods>`

Finding an example usually does not require much imagination. In this
case we just took the values from the first customer and changed the
name to the generic "Jane Doe".

These examples are entirely optional. If you cannot find a good example
for a field (like one containing a database BLOB) or you do not think
a real world example does not add any value (like for a field
containing an encrypted password), feel free to leave it empty.

Allowing fields to be empty
===========================

So far, every data item had an actual value and none of it was empty.
But what if for instance we do not know the date of birth for one of
our customers? Consider the following example data file:

+---------+-----------+----------+-------+------+-------------+
+Branch id+Customer id+First name+Surname+Gender+Date of birth+
+---------+-----------+----------+-------+------+-------------+
+38000    +16         +Daisy     +Mason  +female+27.02.1946   +
+---------+-----------+----------+-------+------+-------------+
+38000    +42         +Wendy     +Davis  +female+30.12.1971   +
+---------+-----------+----------+-------+------+-------------+
+38000    +57         +Keith     +Parker +male  +02.06.1984   +
+---------+-----------+----------+-------+------+-------------+
+38000    +76         +Kenneth   +Tucker +male  +             +
+---------+-----------+----------+-------+------+-------------+
+38053    +2          +Carlos    +Barrett+male  +09.02.1929   +
+---------+-----------+----------+-------+------+-------------+
+38053    +20         +Terrance  +Hart   +male  +11.03.1961   +
+---------+-----------+----------+-------+------+-------------+
+38053    +34         +Lori      +Dunn   +female+26.09.1996   +
+---------+-----------+----------+-------+------+-------------+
+38053    +73         +Mary      +Sutton +female+09.12.1982   +
+---------+-----------+----------+-------+------+-------------+
+38053    +83         +Lorraine  +Castro +female+15.08.1978   +
+---------+-----------+----------+-------+------+-------------+
+38111    +16         +Esther    +Newman +female+             +
+---------+-----------+----------+-------+------+-------------+
+38111    +79         +Tyler     +Rose   +male  +17.12.1920   +
+---------+-----------+----------+-------+------+-------------+
+38111    +96         +Andrew    +Dixon  +male  +02.10.1913   +
+---------+-----------+----------+-------+------+-------------+

See: :download:`customers_without_date_of_birth.csv <../examples/customers_without_date_of_birth.csv>`

Two customers do not have a date of birth: Kenneth Tucker in row 4 and
Ester Newman in row 10.

Now try to validate these data with the same ICD we used before::

  cutplace icd_customers_1.ods customers_without_date_of_birth.csv

This time the output contains the following lines::

  INFO:cutplace:validate "customers_without_date_of_birth.csv"
  ...
  ERROR:cutplace:items: ['38000', '76', 'Kenneth', 'Tucker', 'male', '']
  ERROR:cutplace:field error: field 'date_of_birth' must match format: value must not be empty
  ...
  ERROR:cutplace:items: ['38111', '16', 'Esther', 'Newman', 'female', '']
  ERROR:cutplace:field error: field 'date_of_birth' must match format: value must not be empty
  ...

The essential part here is::

  field 'date_of_birth' must match format: value must not be empty

When you describe a field to cutplace in the ICD, it assumes that the
data always provide a value for this field. Apparently this is not the
case with the data provided, so cutplace complains about it.

But what if there are actually customers we do not yet know the date of
birth yet? Not every business transactions requires the date of birth,
so this is perfectly valid.

So we have to tell cutplace that this field actually can be empty. This
can easily be done by adding another column to the field description,
where fields that can be empty are marked with an ``X``:

+-+--------------------+----------+----------+
+ +Fields              +          +          +
+-+--------------------+----------+----------+
+ +Name                +Example   +**Empty?**+
+-+--------------------+----------+----------+
+F+branch_id           +38000     +          +
+-+--------------------+----------+----------+
+F+customer_id         +16        +          +
+-+--------------------+----------+----------+
+F+first_name          +Jane      +          +
+-+--------------------+----------+----------+
+F+surname             +Doe       +          +
+-+--------------------+----------+----------+
+F+gender              +female    +          +
+-+--------------------+----------+----------+
+F+date_of_birth       +27.02.1946+**X**     +
+-+--------------------+----------+----------+

See: :download:`icd_customers_with_empty_fields.csv <../examples/icd_customers_with_empty_fields.csv>`
or :download:`icd_customers_with_empty_fields.ods <../examples/icd_customers_with_empty_fields.ods>`

Now lets try again with the new ICD::

  cutplace icd_customers_with_empty_fields.ods customers_without_date_of_birth.csv

This time, no error messages show up and all the data are accepted.

Limiting the length of field values
===================================

Right now we allow the fields to have any length. But what if the data should be
processes by another program, which wants to insert the data in a database?
Every field in the database has a limit on how many characters it can hold. If
there are too many characters, the import will fail. And not always with an
error message that makes it easy to backtrack where the broken data came from.

Fortunately, cutplace allows to describe length limits for fields:

+-+--------------------+----------+------+----------+
+ +Name                +Example   +Empty?+**Length**+
+-+--------------------+----------+------+----------+
+F+branch_id           +38000     +      +**5**     +
+-+--------------------+----------+------+----------+
+F+customer_id         +16        +      +**2:**    +
+-+--------------------+----------+------+----------+
+F+first_name          +Jane      +      +**:60**   +
+-+--------------------+----------+------+----------+
+F+surname             +Doe       +      +**:60**   +
+-+--------------------+----------+------+----------+
+F+gender              +female    +      +**4:6**   +
+-+--------------------+----------+------+----------+
+F+date_of_birth       +27.02.1946+X     +**10**    +
+-+--------------------+----------+------+----------+

See: :download:`icd_customers_with_lengths.csv <../examples/icd_customers_with_lengths.csv>`
or :download:`icd_customers_with_lengths.ods <../examples/icd_customers_with_lengths.ods>`

Let's take a closer look at these examples, especially at the meaning of
the colon (:) in some of the description of the lengths.

* The ``branch_id`` always has to have exactly 5 characters, so its
  length is ``5``.

* Let's assume same the ``customer_id`` has to have at least 2 characters
  because one of them is a checksum in order to catch (most) mistyped
  numbers. In this case, the length is ``2:``.

* The ``first_name`` and ``surname`` can take at most 60 characters, maybe
  because someone said so way back in the 70s when COBOL ruled the world.
  To express this as length, use ``:60``.

* The ``gender`` can be ``male`` or ``female``, so its length is between
  4 and 6, which reads as ``4:6``.

* And finally, ``date_of_birth`` always takes exactly 10 characters
  because apparently we require it to use leading zeros. This is
  similar to ``brach_id``, which also used an exact length.

  Wait a second, didn't we state before that the ``date_of_birth`` can be
  empty? Shouldn't we use ``0:10`` then? Actually no, because this would
  also accept dates with a length of 1, 2, 3 and so on until 9. The
  possibility that ``date_of_birth`` can have a length of 0 is already
  taken care of by the ``X`` in the *Empty?* column.

To summarize: lengths are either exact values (like ``5``) or ranges
with an lower and upper limit separated by a colon (like ``4:6``).
Either the lower or upper limit can be omitted (like ``2:`` or ``:60``).

In case you cannot decide yet on a reasonable limit on a certain field,
just leave its entry in the *Length* column empty.

Now lets try again with the new ICD::

  cutplace icd_customers_with_lengths.ods customers_without_date_of_birth.csv

As expected, all the data are accepted again.

.. TODO: Provide an example data file that causes errors.

Field types and rules
=====================

So far, all the validations have been rather simple and generic. It's
time to reveal the big guns: types and rules.

Let's take a closer look at the ``customer_id``. Apparently, it's a
number. To be more specific, an integer number with no fractional part.
Let's say the same person who told us that a ``customer_id`` has at
least two digits now informed us that due a design stemming from the 16
bit era, the highest ``customer_id`` is 65535 (the largest number one
can represent with 16 bit). Here's how to express this knowledge with
cutplace:

+-+--------------------+----------+------+------+------------+----------------+
+ +Name                +Example   +Empty?+Length+**Type**    +**Rule**        +
+-+--------------------+----------+------+------+------------+----------------+
+F+branch_id           +38000     +      +5     +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+customer_id         +16        +      +2:    +**Integer** +**10:65535**    +
+-+--------------------+----------+------+------+------------+----------------+
+F+first_name          +Jane      +      +:60   +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+surname             +Doe       +      +:60   +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+gender              +female    +      +2:6   +**Choice**  +**male, female**+
+-+--------------------+----------+------+------+------------+----------------+
+F+date_of_birth       +27.02.1946+X     +10    +**DateTime**+**DD.MM.YYYY**  +
+-+--------------------+----------+------+------+------------+----------------+

See: :download:`icd_customers_with_types_and_rules.csv <../examples/icd_customers_with_types_and_rules.csv>`
or :download:`icd_customers_with_types_and_rules.ods <../examples/icd_customers_with_types_and_rules.ods>`

The column *Type* can contain one of several available types. The column
*Rule* can hold a text that gives further details about the *Type*.

.. warning::

  Type names are case sensitive. So when you specify a type, make sure
  the letters match exactly concerning upper and lower case.

In case of ``customer_id``, the type is ``Integer``. In this case, the
rule can specify a valid range. The syntax for the range is the same
we've been using already for the *Length* column. So ``10:65535`` means
"between 10 and 65535".

For ``gender``, the type is ``Choice`` which means that every value in
this field must be in a list of possible choices specified with the
rule. Here, possible choices are ``male`` and ``female``.

Finally ``date_of_birth`` is of type ``DateTime``. The rule describes
the date format using place holders: ``DD`` (day), ``MM`` (month),
``YYYY`` (year including century) and ``YY`` (year without century). Any
other character must show up literally, for example the ``.`` in the
rule must show up as ``.`` in the value.

This tutorial showcases just a few of the types available.

.. seealso::

  :ref:`field-format-decimal`
    A field format to describe decimal numbers with a fractional part.

  :ref:`field-format-pattern`
    A field format to match patterns using asterisk (*) and question
    mark (?) as placeholders.

  :ref:`field-format-regex`
    A field format to match patterns using regular expressions.

Checking general conditions
===========================

So far we learned how to validate the general data format and values
of separate fields. But what about conditions that are more sophisticated
and require several fields or rows to validate them?

For example, we might want to validate that every customer has a unique
``customer_id`` within its assigned branch.

Or we might want to validate that the number of distinct branches does
remain within a certain limit, say, 3 branches.

For these kind of conditions cutplace supports *checks*. Here's how it
looks in practice:

+-+--------------------------------------+-------------+----------------------+
+ +Checks                                +             +                      +
+-+--------------------------------------+-------------+----------------------+
+ +*Description*                         +*Type*       +*Rule*                +
+-+--------------------------------------+-------------+----------------------+
+C+customer must be unique               +IsUnique     +branch_id, customer_id+
+-+--------------------------------------+-------------+----------------------+
+C+distinct branches must be within limit+DistinctCount+branch_id <= 3        +
+-+--------------------------------------+-------------+----------------------+

See: :download:`icd_customers.csv <../examples/icd_customers.csv>`
or :download:`icd_customers.ods <../examples/icd_customers.ods>`

As you can see, checks require a "C" in the first column.

Next there is a description of the check. This should be a meaningful
sentence because it shows up in error messages. It's a good idea to word
them as "Something must be something else" sentences.

The remaining two columns contain the type of the check and the rule. How
the rule can look solely depends on the type of the check.

.. seealso::

  :ref:`check-distinct-count`
    A check to validate that the number of distinct values in a field
    meets a specified condition.

  :ref:`check-is-unique`
    A check to validate that a field value or a combination of field
    values is unique in each row compared with all other rows.

.. index:: cutsniff

.. _cutsniff:

Sniffing drafts from data
=========================

Creating ICDs from scratch by looking at a file and deducing the basic data
format and field properties from it is a rather cumbersome task. That's
where ``cutsniff`` comes in: it takes a look at a data file, and creates an
ICD for it.

The resulting ICD can be used for validation immediately, though it is
recommeneded that you rework it to some extend. Nevertheless within seconds
you get an ICD that can immediately be used and possibly improved later on.

As example, consider our data file ``examples/customers.csv``. To make
``cutsniff`` create an ICD for it, run::

  cutsniff icd_customers_sniffed.csv examples/customers.csv

The resulting ``icd_customers_sniffed.csv`` looks like this::

  Interface: <Name>

  d,format,delimited
  d,item delimiter,","
  d,line delimiter,lf
  d,escape character,""""
  d,quote character,""""
  d,encoding,ascii

  ,Field,Example,Empty?,Length,Type,Rule
  f,column_a,,,5,Text,
  f,column_b,,,2,Text,
  f,column_c,,,4,Text,
  f,column_d,,,3:7,Text,
  f,column_e,,,4:6,Text,
  f,column_f,,,10,Text,

You can already use this to validate the data::

  cutplace icd_customers_sniffed.csv examples/customers.csv

Nevertheless most sniffed ICDs will need manual tweaking before you can
apply them for other files. In particular, you should:

* Replace the heading ``Interface: <Name>`` by something more meaningful
  so that you can quickly grasp the intent of the data the interface
  describes.
* Change the field names to something more meaningful than ``column_*`` in
  order to understand the meaning of it.
* Change the expected length of fields in order to validate other data
  files that might contain longer or shorter values.
* Save the ICD as ODS or Excel and make it easier to read by utilizing
  colors and formatting

In case the data file starts with a heading, you can exclude it from the
analysis using ``--head``.

If CSV or PRN data files use an ecoding other than ASCII, you can specify
it using ``--data-encoding``.

For example::

  cutplace --head 1 --data-encoding iso-8859-15 icd_customers_sniffed.csv examples/valid_customers_with_header_iso-8859-15.csv

In case ``--head`` is specified, ``cutsniff`` uses the last header row to
derive field names by applying a couple of heuristics to turn them into
valid Python variable names.

If you prefer to set the field names already during sniffing instead of
manually adjusting them afterwards, you can use ``--names`` to specify a
comma separated list of names. For example::

  cutplace --head 1 --names "branchId,customerId,firstName,surName,gender,dateOfBirth" ...

To get an overview of all command line options available, run::

  cutsniff --help

Conclusion
==========

You are now familiar with the basic concepts behind cutplace and should
be able to use this for writing reasonably complete and sophisticated
ICDs.
