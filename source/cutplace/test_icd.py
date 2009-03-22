"""Tests for interface control documents."""
import checks
import icd
import logging
import StringIO
import unittest

def createDefaultTestIcd(lineDelimiter="\n"):
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
"F","gender","Choice",,,"female, male, other, unknown","male"
"F","date_of_birth","DateTime",,,"DD.MM.YYYY",08.03.1957
,,,,,,
,"Constraints",,,,,
,,,,,,
,"Description","Type","Rule",,,
"C","customer must be unique","IsUnique","branch_id, customer_id",,,
"C","number of branches must be in range","DistinctCount","branch_id < 10",,,
"""
    spec = spec.replace("\n", lineDelimiter)
    result = icd.InterfaceDescription()
    result.read(StringIO.StringIO(spec))
    return result
        

class InterfaceControlDocumentTest(unittest.TestCase):
    """Tests  for InterfaceControlDocument."""

    def testSimpleIcd(self):
        createDefaultTestIcd("\n")
        createDefaultTestIcd("\r")
        createDefaultTestIcd("\r\n")
        
    def testIsUniqueCheck(self):
        icd = createDefaultTestIcd()
        data = """38000,23,"John","Doe","male","08.03.1957"
38000,59,"Jane","Miller","female","04.10.1946"
38000,23,"Mike","Webster","male","23.12.1974" """
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.DEBUG)
    logging.getLogger("cutplace.test_idc").setLevel(logging.INFO)
    unittest.main()
