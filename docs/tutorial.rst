.. _tutorial:

========
Tutorial
========

This chapter gives a gentle introduction and overview to cutplace. It
introduces a simple set of example data and shows how to write a simple
cutplace interface definition (CID) for it which can be used to validate
the data. Starting from there, the CID gets refined and improved to
allow more rigorous validations which detect increasingly subtle errors
in the data.

You can find the files for the examples in the :file:`examples` folder of
the cutplace source distribution. For your convenience they are also
provided as links at the bottom of each data or CID file.

A simple set of customer data
=============================

In order to make use of cutplace, you need some data. For this tutorial,
we will use a simple set of customer data:

.. literalinclude:: ../examples/customers.csv

See: :download:`customers.csv <../examples/customers.csv>`

Because this is hard to read here is how the file looks if you
open it in a spreadsheet application such as Excel or Calc:

.. include:: ../docs/include/customers.rst

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
+F+customer_id        +   +
+-+-------------------+---+
+F+first_name         +   +
+-+-------------------+---+
+F+surname            +   +
+-+-------------------+---+
+F+date_of_birth      +   +
+-+-------------------+---+
+F+gender             +   +
+-+-------------------+---+

See: :download:`cid_customers_field_names_only.ods <../examples/cid_customers_field_names_only.ods>`

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
  when cutplace attempts to read the CID.

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

As already pointed out, if a row in the CID starts with an empty column,
cutplace skips it without processing in any way. Actually, this would
mean the same for cutplace:

+-+-------------------+---+
+D+Format             +CSV+
+-+-------------------+---+
+D+Header             +1  +
+-+-------------------+---+
+F+customer_id        +   +
+-+-------------------+---+
+F+first_name         +   +
+-+-------------------+---+
+F+surname            +   +
+-+-------------------+---+
+F+date_of_birth      +   +
+-+-------------------+---+
+F+gender             +   +
+-+-------------------+---+

But it's a lot harder to read, isn't it?

How and where to store the CID
==============================

So how do you store this information? Cutplace is quite flexible here.
The easiest way would be to use a spreadsheet application such as Excel
or OpenOffice.org's Calc and store it as :file:`*.xlsx` or :file:`*.ods`
file. Alternatively you can use the text editor or your choice and store it
as UTF-8 encoded :file:`*.csv`, where columns are separated with a comma (,)
and data items with blanks or commas are embedded between double quotes (").

Concerning the location on your disk, cutplace does not impose any
requirements on you.

.. TODO: Recommendations how to name the CID files.

For this tutorial, we assume both the data and CID files are stored in
the same folder which and that your current console terminal session already
changed to this folder (using for example the command :command:`cd`).

Running cutplace for the first time
===================================

Now that we have both a data file and a CID file, we can finally take a look
at how cutplace actually works.

Open a terminal and change into the folder where where the example data
and CID files are located::

  cd .../where/ever/examples

Next let's try if cutplace has been installed properly::

  cutplace --version

This should result in an output similar to::

  cutplace 0.8.x

The actual version numbers may vary. If your version of cutplace is older then
|release|, consider upgrading to avoid compatibility issues with this
tutorial.

If instead this results in an error message, refer to the chapter on
:doc:`installation` about how to setup cutplace.

In case everything worked out so far, let's finally do what we came here
for: validate that our data conform to the interface we just described::

  cutplace cid_customers_field_names_only.ods customers.csv

This assumes you used Calc to create the CID. Users of Excel should
replace the ":file:`.ods`" with ":file:`.xlsx`", users of text editors with
":file:`.csv`" respectively.

Summary so far
==============

Let's recap what we learned so far:

* You can use cutplace to validate that data conform to a CID.

* The CID is a file you can create with Calc, Excel or your favorite
  text editor.

* As a minimum, the CID has to specify the data format and the name of
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
+F+customer_id         +**1**         +
+-+--------------------+--------------+
+F+surname             +**Doe**       +
+-+--------------------+--------------+
+F+first_name          +**Jane**      +
+-+--------------------+--------------+
+F+date_of_birth       +**1995-11-15**+
+-+--------------------+--------------+
+F+gender              +**female**    +
+-+--------------------+--------------+

See: :download:`cid_customers_with_examples.ods <../examples/cid_customers_with_examples.ods>`

Finding an example usually does not require much imagination. In this
case we just took the values from the first customer and changed the
name to the generic "Jane Doe".

These examples are entirely optional. If you cannot find a good example
for a field (like one containing a database BLOB) or you do not think
a real world example does not add any value (like a field containing an
encrypted password), feel free to leave it empty.

Allowing fields to be empty
===========================

So far, every data item had an actual value and none of it was empty.
But what if for instance we do not know the date of birth for one of
our customers? Consider the following example data file:

.. include:: ../docs/include/customers_without_date_of_birth.rst

See: :download:`customers_without_date_of_birth.csv <../examples/customers_without_date_of_birth.csv>`

Two customers do not have a date of birth: Kenneth Tucker in row 4 and
Ester Newman in row 10.

Now try to validate these data with the same CID we used before::

  cutplace cid_customers_field_names_only.ods customers_without_date_of_birth.csv

This time the output contains the following lines::

  INFO:cutplace:validate "examples/customers_without_date_of_birth.csv"
  ERROR:cutplace:  customers_without_date_of_birth.csv (R4C4): cannot accept field 'date_of_birth': value must not be empty

The essential part here is::

  field 'date_of_birth' must match format: value must not be empty

When you describe a field to cutplace in the CID, it assumes that the
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
+F+customer_id         +16        +          +
+-+--------------------+----------+----------+
+F+first_name          +Jane      +          +
+-+--------------------+----------+----------+
+F+surname             +Doe       +          +
+-+--------------------+----------+----------+
+F+date_of_birth       +1995-11-15+**X**     +
+-+--------------------+----------+----------+
+F+gender              +female    +**X**     +
+-+--------------------+----------+----------+

See: :download:`cid_customers_with_empty_fields.ods <../examples/cid_customers_with_empty_fields.ods>`

Now lets try again with the new CID::

  cutplace cid_customers_with_empty_fields.ods customers_without_date_of_birth.csv

This time, no error messages show up and all the data are accepted::

  INFO:cutplace:validate "customers_without_date_of_birth.csv"
  INFO:cutplace:  accepted 10 rows


Limiting the length of field values
===================================

Right now we allow the fields to have any length. But what if the data should be
processes by another program, which wants to insert the data in a database?
Every field in the database has a limit on how many characters it can hold. If
there are too many characters, the import will fail. And not always with an
error message that makes it easy to backtrack where the broken data came from.

Fortunately, cutplace allows to describe length limits for fields:

+-+--------------------+----------+------+------------+
+ +Name                +Example   +Empty?+**Length**  +
+-+--------------------+----------+------+------------+
+F+customer_id         +16        +      +**2...**    +
+-+--------------------+----------+------+------------+
+F+first_name          +Jane      +      +**...60**   +
+-+--------------------+----------+------+------------+
+F+surname             +Doe       +      +**...60**   +
+-+--------------------+----------+------+------------+
+F+date_of_birth       +1995-11-15+X     +**10**      +
+-+--------------------+----------+------+------------+
+F+gender              +female    +X     +**4...6**   +
+-+--------------------+----------+------+------------+

See: :download:`cid_customers_with_lengths.ods <../examples/cid_customers_with_lengths.ods>`

Let's take a closer look at these examples, especially at the meaning of
the ellipsis (...) in some of the description of the lengths.

* Let's assume same the ``customer_id`` has to have at least 2 characters
  because one of them is a checksum in order to catch (most) mistyped
  numbers. In this case, the length is ``2...``.

* The ``first_name`` and ``surname`` can take at most 60 characters, maybe
  because someone said so way back in the 70s when COBOL ruled the world.
  To express this as length, use ``...60``.

* The ``date_of_birth`` always takes exactly 10 characters because apparently
  we require it to use leading zeros.

  Wait a second, didn't we state before that the ``date_of_birth`` can be
  empty? Shouldn't we use ``0...10`` then? Actually no, because this would
  also accept dates with a length of 1, 2, 3 and so on until 9. The
  possibility that ``date_of_birth`` can have a length of 0 is already
  taken care of by the ``X`` in the *Empty?* column.

* And finally, the ``gender`` can be ``male`` or ``female``, so its length is between
  4 and 6, which reads as ``4...6``.

To summarize: lengths are either exact values (like ``10``) or ranges with a
lower and upper limit separated by a colon (like ``4...6``). Either the lower
or upper limit can be omitted (like ``2...`` or ``...60``).

In case you cannot decide yet on a reasonable limit on a certain field,
just leave its entry in the *Length* column empty.

Now lets try again with the new CID::

  cutplace cid_customers_with_lengths.ods customers_without_date_of_birth.csv

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
+F+customer_id         +16        +      +2:    +**Integer** +**10...65535**  +
+-+--------------------+----------+------+------+------------+----------------+
+F+first_name          +Jane      +      +:60   +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+surname             +Doe       +      +:60   +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+date_of_birth       +1995-11-15+X     +10    +**DateTime**+**YYYY-MM-DD**  +
+-+--------------------+----------+------+------+------------+----------------+
+F+gender              +female    +X     +2:6   +**Choice**  +**male, female**+
+-+--------------------+----------+------+------+------------+----------------+

See: :download:`cid_customers_with_types_and_rules.ods <../examples/cid_customers_with_types_and_rules.ods>`

The column *Type* can contain one of several available types. The column
*Rule* can hold a text that gives further details about the *Type*.

.. warning::

  Type names are case sensitive. So when you specify a type, make sure
  the letters match exactly concerning upper and lower case.

In case of ``customer_id``, the type is ``Integer``. In this case, the
rule can specify a valid range. The syntax for the range is the same
we've been using already for the *Length* column. So ``10...65535``
means "between 10 and 65535".

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
``customer_id``.

For these kind of conditions cutplace supports *checks*. Here's how it
looks in practice:

+-+--------------------------------------+-------------+----------------------+
+ +Checks                                +             +                      +
+-+--------------------------------------+-------------+----------------------+
+ +*Description*                         +*Type*       +*Rule*                +
+-+--------------------------------------+-------------+----------------------+
+C+customer must be unique               +IsUnique     +customer_id           +
+-+--------------------------------------+-------------+----------------------+

See: :download:`cid_customers.ods <../examples/cid_customers.ods>`

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

It is also possible to check for composite keys spawning several fields. As an
example consider multiple branches of a company where each branch can have a
customer with a ``customer_id`` of for example ``16``:

+-+--------------------+----------+------+------+------------+----------------+
+ +Name                +Example   +Empty?+Length+Type        +Rule            +
+-+--------------------+----------+------+------+------------+----------------+
+F+**branch_id**       +123       +      +1...  +Integer     +1...99999       +
+-+--------------------+----------+------+------+------------+----------------+
+F+customer_id         +16        +      +2...  +Integer     +10...65535      +
+-+--------------------+----------+------+------+------------+----------------+
+F+first_name          +Jane      +      +...60 +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+surname             +Doe       +      +...60 +            +                +
+-+--------------------+----------+------+------+------------+----------------+
+F+date_of_birth       +1995-11-15+X     +10    +DateTime    +YYYY-MM-DD      +
+-+--------------------+----------+------+------+------------+----------------+
+F+gender              +female    +X     +2...6 +Choice      +male, female    +
+-+--------------------+----------+------+------+------------+----------------+

To check that the customer_id is unique within each branch, use:

+-+--------------------------------------+-------------+-----------------------+
+ +Description                           +Type         +Rule                   +
+-+--------------------------------------+-------------+-----------------------+
+C+customer must be unique within branch +IsUnique     +branch_id, customer_id +
+-+--------------------------------------+-------------+-----------------------+

Possibly branches are 5 digit codes however in practice it might be known that
there are at most 100 branches at the same time. To express this, use:

+-+---------------------------------------+--------------+-----------------+
+ +Description                            +Type          +Rule             +
+-+---------------------------------------+--------------+-----------------+
+C+distinct branches must be within limit +DistinctCount +branch_id <= 100 +
+-+---------------------------------------+--------------+-----------------+


Conclusion
==========

You are now familiar with the basic concepts behind cutplace and should
be able to use this for writing reasonably complete and sophisticated
CIDs.
