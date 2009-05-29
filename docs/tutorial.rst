================
Tutorial
================

This chapter introduces gives a gently introduction and overview to cutplace.
It introduces a simple set of example data and shows how to write a simple
interface control document (ICD) for it which can be used to validate the
data. Starting from there, the ICD gets refined and improved to allow more
rigorous validations which detect increasingly subtle errors in the data.

A simple set of customer data
=============================

In order to make use of cutplace, you need some data. For this tutorial,
we will use a simple set of customer data:

.. literalinclude:: ../examples/customers_1.csv
   :lines: 2-

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

TODO: Actually explain cutplace.