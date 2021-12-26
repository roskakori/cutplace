.. image:: https://img.shields.io/pypi/v/cutplace
    :target: https://pypi.org/project/cutplace/
    :alt: PyPI

.. image:: https://readthedocs.org/projects/cutplace/badge/?version=latest
    :target: https://cutplace.readthedocs.io/
    :alt: Documentation

.. image:: https://github.com/roskakori/cutplace/actions/workflows/build.yaml/badge.svg
    :target: https://travis-ci.org/roskakori/cutplace
    :alt: Build Status

.. image:: https://coveralls.io/repos/roskakori/cutplace/badge.png?branch=master
    :target: https://coveralls.io/r/roskakori/cutplace?branch=master
    :alt: Test coverage

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black

Cutplace is a tool and API to validate that tabular data stored in CSV,
Excel, ODS and PRN files conform to a cutplace interface definition (CID).

As an example, consider the following ``customers.csv`` file that stores data
about customers::

    customer_id,surname,first_name,born,gender
    1,Beck,Tyler,1995-11-15,male
    2,Gibson,Martin,1969-08-18,male
    3,Hopkins,Chester,1982-12-19,male
    4,Lopez,Tyler,1930-10-13,male
    5,James,Ana,1943-08-10,female
    6,Martin,Jon,1932-09-27,male
    7,Knight,Carolyn,1977-05-25,female
    8,Rose,Tammy,2004-01-12,female
    9,Gutierrez,Reginald,2010-05-18,male
    10,Phillips,Pauline,1960-11-09,female

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
Excel and ODS, for example ``cid_customers.ods``.

Cutplace can validate that the data file conforms to the CID::

    $ cutplace cid_customers.ods customers.csv

Now add a new line with a broken ``date_of_birth``::

    73921,Harris,Diana,04.08.1953,female

Cutplace rejects this file with the error message:

    customers.csv (R12C4): cannot accept field 'date_of_birth': date must
    match format YYYY-MM-DD (%Y-%m-%d) but is: '04.08.1953'

Additionally, cutplace provides an easy to use API to read and write
tabular data files using a common interface without having to deal with
the intrinsic of data format specific modules. To read and validate the
above example::

    import cutplace
    import cutplace.errors

    cid_path = 'cid_customers.ods'
    data_path = 'customers.csv'
    try:
        for row in cutplace.rows(cid_path, data_path):
            pass  # We could also do something useful with the data in ``row`` here.
    except cutplace.errors.DataError as error:
        print(error)

For more information, read the documentation at
http://cutplace.readthedocs.org/ or visit the project at
https://github.com/roskakori/cutplace.
