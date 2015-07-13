.. image:: https://pypip.in/py_versions/cutplace/badge.svg
    :target: https://pypi.python.org/pypi/cutplace/
    :alt: Supported Python versions

.. image:: https://pypip.in/format/cutplace/badge.svg
    :target: https://pypi.python.org/pypi/cutplace/
    :alt: Download format

.. image:: https://pypip.in/license/cutplace/badge.svg
    :target: https://pypi.python.org/pypi/cutplace/
    :alt: License

.. image:: https://travis-ci.org/roskakori/cutplace.svg?branch=master
    :target: https://travis-ci.org/roskakori/cutplace
    :alt: Build Status

.. image:: https://coveralls.io/repos/roskakori/cutplace/badge.png?branch=master
    :target: https://coveralls.io/r/roskakori/cutplace?branch=master
    :alt: Test coverage

.. image:: https://landscape.io/github/roskakori/cutplace/master/landscape.svg
    :target: https://landscape.io/github/roskakori/cutplace/master
    :alt: Code Health

Cutplace is a tool and API to validate that tabular data stored in CSV,
Excel, ODS and PRN files conform to an cutplace interface definition (CID).

As an example, consider the following ``customers.csv`` file that stores data
about customers::

    ID,surname,first_name,born,gender
    3798,Miller,John,1978-11-27,male
    19253,Webster Inc.,,1950-01-12,
    46418,Jane,Doe,2003-06-29,female

A CID can describe such a file in an easy to read way. It consists of
three sections. First, there is the general data format:

==  ==============  ===========
..  Property        Value
==  ==============  ===========
D   Format          Delimited
D   Encoding        UTF-8
D   Header          1
D   Line delimiter  LF
D   Item delimiter  ,
==  ==============  ===========

Next there are the fields stored in the data file:

==  =============  ==========  =====  ======  ========  ==============================
..  Name           Example     Empty  Length  Type      Rule
==  =============  ==========  =====  ======  ========  ==============================
F   customer_id    3798                       Integer   0...99999
F   surname        Miller             ...60
F   first_name     John        X      ...60
F   date_of_birth  1978-11-27                 DateTime  YYYY-MM-DD
F   gender         male        X              Choice    female, male
==  =============  ==========  =====  ======  ========  ==============================

Optionally you can describe conditions that must be met across the whole file:

==  =======================  ========  ===========
..  Description              Type      Rule
==  =======================  ========  ===========
C   customer must be unique  IsUnique  customer_id
==  =======================  ========  ===========

The CID can be stored in common spreadsheet formats, in particular
Excel and ODS, for example ``customers_cid.ods``.

Cutplace can validate that the data file conforms to the CID::

    $ cutplace customers_cid.ods customers.csv

Now add a new line with a broken ``date_of_birth``::

    73921,Harris,Diana,04.08.1913,female

Cutplace rejects this file with the error message:

    customers.csv (R5C4): cannot accept field 'date_of_birth': date must
    match format YYYY-MM-DD (%Y-%m-%d) but is: '04.08.1913'

Additionally, cutplace provides an easy to use API to read and write
tabular data files using a common interface without having to deal with
the intrinsic of data format specific modules. To read and validate the
above example::

    import cutplace
    import cutplace.errors

    cid_path = 'customers_cid.ods'
    data_path = 'customers.csv'
    try:
        for row in cutplace.rows(cid_path, data_path):
            pass  # We could also do something useful with the data in ``row`` here.
    except cutplace.errors.DataError as error:
        print(error)

For more information, read the documentation at
http://cutplace.readthedocs.org/ or visit the project at
https://github.com/roskakori/cutplace.
