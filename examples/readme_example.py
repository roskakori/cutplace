"""
Example for validated reading as used in the README.
"""
import cutplace
import cutplace.errors

cid_path = 'cid_customers.ods'
data_path = 'customers.csv'
try:
    for row in cutplace.rows(cid_path, data_path):
        pass  # We could also do something useful with the data in ``row`` here.
except cutplace.errors.DataError as error:
    print(error)
