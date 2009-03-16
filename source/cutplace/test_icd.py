"""Tests for interface control documents."""
import icd
import logging
import StringIO
import unittest

class InterfaceControlDocumentTest(unittest.TestCase):
    """Tests  for DateTimeFieldFormat."""
    def testSimpleIcd(self):
        spec = ""","Interface: customer",,,,,
,,,,,,
,"Data format",,,,,
,,,,,,
"D","Format","CSV",,,,
"D","Line delimiter","LF",,,,
"D","Item delimiter",",",,,,
"D","Encoding","ISO-8859-1",,,,
"D","Allowed characters","32...",,,,
,,,,,,
,"Fields",,,,,
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","customer_id","Integer",,,"0...99999",12345
"F","first_name","Text","X",,,"John"
"F","surname","Text",,"1...60",,"Doe"
"F","gender","Choice",,,"male, female, unknown","male"
"F","date_of_birth","DateTime",,,"DD.MM.YYYY",08.03.1957
,,,,,,
,,,,,,
,"Constraints",,,,,
,,,,,,
,"Description","Type","Rule",,,
"C","customer must be unique","IsUnique","branch_id, customer_id",,,
"""
        testIcd = icd.InterfaceDescription()
        testIcd.read(StringIO.StringIO(spec))
        # TODO: Test with CRLF as line delimiter

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.test_idc").setLevel(logging.INFO)
    unittest.main()
