#!/bin/sh
set -e
echo "🏗️ Building include files"
python tests/dev_torst.py examples/cid_customers.ods examples/customers.csv docs/include/customers.rst
python tests/dev_torst.py examples/cid_customers.ods examples/customers_without_date_of_birth.csv docs/include/customers_without_date_of_birth.rst
echo "📖 Building documentation"
make -C docs html
echo "🎉 Successfully built documentation in docs/_build/html/index.html"
