# -*- coding: iso-8859-1 -*-
"""Tests for interface control documents."""
import checks
import interface
import logging
import StringIO
import unittest

def createDefaultTestFixedIcd():
    spec = """,Interface: customer,,,,,         System/
,,,,,,ight-V100/                  Users/
,Data format,,,,,                 Volumes/
,,,,,,pple.timemachine.supported  bin/
D,Format,Fixed,,,,                cores/
D,Line delimiter,any,,,,          dev/
D,Encoding,ISO-8859-1,,,,         etc/
D,Allowed characters,32...,,,,    home/
,,,,,,/                           mach_kernel
,Fields,,,,,                      mach_kernel.ctfsys
,,,,,,p DF                        net/
,Name,Type,Empty,Length,Rule,Examplet/
F,branch_id,RegEx,,5,38\d\d\d,38123rivate/
F,customer_id,Integer,,5,0...99999,12345
F,first_name,Text,X,15,,John      tmp/
F,surname,Text,,15,,Doe           usr/
F,gender,Choice,,7,"male, female, unknown",male
F,date_of_birth,DateTime,,10,DD.MM.YYYY,08.03.1957
,,,,,,
,Checks,,,,,
,,,,,,
,Description,Type,Rule,,,
C,customer must be unique,IsUnique,"branch_id, customer_id",,,
C,distinct branches must be within limit,DistinctCount,branch_id <= 3,,,
"""
    result = interface.InterfaceControlDocument()
    result.read(StringIO.StringIO(spec))
    return result

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
    result = interface.InterfaceControlDocument()
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

    def testLatin1(self):
        icd = createDefaultTestIcd()
        data = """38000,23,"John","Doe","male","08.03.1957"
38000,59,"Bärbel","Müller","female","04.10.1946"
38000,23,"Mike","Webster","male","23.12.1974" """
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)
        
    def testSimpleFixedIcd(self):
        icd = createDefaultTestFixedIcd()
        data = "3800012345John           Doe            male   08.03.19573800012346Jane           Miller         female 04.10.1946"
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)
        
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.DEBUG)
    logging.getLogger("cutplace.test_idc").setLevel(logging.INFO)
    unittest.main()
