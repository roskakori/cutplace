================
Tutorial
================

This chapter gives a gently introduction and overview to cutplace. It
introduces a simple set of example data and shows how to write a simple
interface control document (ICD) for it which can be used to validate
the data. Starting from there, the ICD gets refined and improved to
allow more rigorous validations which detect increasingly subtle errors
in the data.

You can find the files for the examples in the ``examples`` folder of
the cutplace source distrubution. For your conveniance they are also
provided as links at the bottom of each data or ICD file.

A simple set of customer data
=============================

In order to make use of cutplace, you need some data. For this tutorial,
we will use a simple set of customer data:

.. literalinclude:: ../examples/customers_1.csv
   :lines: 2-

Example file: `customers_1.csv <customers_1.csv>`_

Because this is hard to read here is how the file looks if you
open it in a spreadsheet application such as Excel or Calc and add headings:

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
+38111    +31         +Esther    +Newman +female+23.03.1932   +
+---------+-----------+----------+-------+------+-------------+
+38111    +79         +Tyler     +Rose   +male  +17.12.1920   +
+---------+-----------+----------+-------+------+-------------+
+38111    +96         +Andrew    +Dixon  +male  +02.10.1913   +
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

Example files: 
`icd_customers_1.ods <icd_customers_1.ods>`_ or
`icd_customers_1.csv <icd_customers_1.csv>`_.

Let's take a closer look at this.

Row 1 is a heading that simply describes what the document is a but:
the interface for customer data.

Row 3 is a section heading to point out that the description of the data
format is about to follow.

Row 4 describes actually the data format by stating that the ``Format``
is ``CSV``. Did you notice the ``D`` in the first column? This is a hint for
cutplace that the row contains information about the data format it should be
able to process.

Row 6 again is a section heading, this time pointing out that descriptions about 
the field formats are about to follow.

The remaining rows then describe the fields that data files must have. So far we only
describe the name of the field, for example ``customer_id``. 

.. note::
  A field name must contain only ASCII letters, numbers and underscore
  (_). So blanks, foreigen characters such as umlauts and
  interpuntuations are not allowed and will result in an error message
  when cutplace attempts to read the ICD.
  
  Some examples for valid field names:
  
  * ``customer_id``
  
  * ``iso_5218_gender``
  
  * ``CustomerId``

  For comparison, here are a few broken field names
  
  * ``customer-id`` - error: contains interpunctuation character "``-``";
    use "``_``" instead.
  
  * ``customer id``  - error: contains a blank; use "``_``" instead.
  
  * ``123easy`` - error: starts with a numeric digits; use a letter as
    first character.

How and where to store the ICD
==============================

So how do you store this information? Cutplace is quite flexible here.
The easiest way would be to use a spreadsheet application such as Excel
or OpenOffice.org's Calc and store it as a ``*.ods`` or ``*.xls`` file.
Alternatively you can use the text editor or your choice and store it as
``*.csv``, where columns are separated with a comma (,) and data items
with blanks or commas are embedded between double quotes (").

Concerning the location on your disk, cutplace does not impose any
requirements on you

TODO: Recommendations how to name the ICD files.

For this tutorial, we assume both the data and ICD files are stored in
the same folder which and your current console terminal session already
changed to this folder (using for example the command ``cd``).

Running cutplace for the first time
===================================

Now that we have both a data and an ICD file, we can finally take a look
at how cutplace actually works.

TODO: elaborate

Summary so far
==============

Let's recap what we learned so far:

* 



Actually, this would mean the same for cutplace:

+-+-------------------+---+
+D+Format             +CSV+
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