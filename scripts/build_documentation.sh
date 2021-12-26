#!/bin/sh
set -e
python tests/dev_torst.py examples/cid_customers.ods examples/customers.csv docs/include/customers.rst
python tests/dev_torst.py examples/cid_customers.ods examples/customers_without_date_of_birth.csv docs/include/customers_without_date_of_birth.rst
make -C docs html
