# -*- coding: iso-8859-1 -*-
"""Tests for interface control documents."""
import checks
import data
import fields
import interface
import logging
import StringIO
import unittest

def createDefaultTestFixedIcd():
    spec = """,Interface: customer,,,,,
,,,,,,
,Data format,,,,,
,,,,,,
D,Format,Fixed,,,,
D,Line delimiter,any,,,,
D,Encoding,ISO-8859-1,,,,
D,Allowed characters,32:,,,,
,,,,,,
,Fields,,,,,
,,,,,,
,Name,Type,Empty,Length,Rule,Example
F,branch_id,RegEx,,5,38\d\d\d,38123
F,customer_id,Integer,,5,0:99999,12345
F,first_name,Text,X,15,,John
F,surname,Text,,15,,Doe
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
"D","Allowed characters","32:",,,,
,,,,,,
,"Fields",,,,,
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","customer_id","Integer",,,"0:99999",12345
"F","first_name","Text","X",,,"John"
"F","surname","Text",,"1:60",,"Doe"
"F","gender","Choice",,,"female, male, other, unknown","male"
"F","date_of_birth","DateTime",,,"DD.MM.YYYY",08.03.1957
,,,,,,
,"Checks",,,,,
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

    def testEmptyChoice(self):
        spec = ""","Interface with a Choice field (gender) that can be empty"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule"
"F","first_name","Text","X",,,"John"
"F","gender","Choice",X,,"female, male","male"
"F","date_of_birth","DateTime",,,"DD.MM.YYYY",08.03.1957
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        data = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)
    
    def testFieldTypeWithModule(self):
        spec = ""","Interface with field using a fully qualified type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule"
"F","first_name","fields.Text","X",,,"John"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        data = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)
    
    def testEmptyChoiceWithLength(self):
        spec = ""","Interface with a Choice field (gender) that can be empty and has a field length > 0"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule"
"F","first_name","Text","X",,,"John"
"F","gender","Choice",X,4:6,"female, male","male"
"F","date_of_birth","DateTime",,,"DD.MM.YYYY",08.03.1957
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        data = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(data)
        icd.validate(dataReadable)
    
    def _testBroken(self, spec, expectedError):
        assert spec is not None
        assert expectedError is not None
        icd = interface.InterfaceControlDocument()
        self.assertRaises(expectedError, icd.read, StringIO.StringIO(spec))
        
    def testBrokenDataFormatInvalidFormat(self):
        spec = ""","Broken Interface with invalid data format"
"D","Format","XYZ"
"""
        self._testBroken(spec, data.DataFormatSyntaxError)
        
    def testBrokenDataFormatInvalidFormatPropertyName(self):
        spec = ""","Broken Interface with invalid data format"
"D","Fromat","XYZ"
"""
        self._testBroken(spec, data.DataFormatSyntaxError)
        
    def testBrokenDataFormatAfterField(self):
        spec = ""","Broken Interface with specified after first field"
"F","branch_id","Text"
"D","Format","XYZ"
"""
        self._testBroken(spec, data.DataFormatSyntaxError)
        
    def testBrokenFieldNameMissing(self):
        spec = ""","Broken Interface with missing field name"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","","Integer",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        spec = ""","Broken Interface with missing field name"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","     ","Integer",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        
    def testBrokenFieldTypeMissing(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","customer_id","",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","branch_id","RegEx",,,"38\d\d\d",38123
"F","customer_id","     ",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmptyModule(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","first_name",".Text","X",,,"John"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmptyClass(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","first_name","fields.","X",,,"John"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmtySubModule(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","first_name","fields..Text","X",,,"John"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldNameWithInvalidCharacters(self):
        spec = ""","Broken Interface with field name containing invalid characters"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","först_name","Text","X",,,"John"
"F","customer_id","",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWithMultipleWord(self):
        spec = ""","Broken Interface with field name containing invalid characters"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Type","Empty","Length","Rule","Example"
"F","first_name","Text and text again","X",,,"John"
"F","customer_id","",,,"0:99999",12345
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        
    def testBrokenInterfaceWithoutFields(self):
        spec = ""","Broken Interface without fields"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
"""
        self._testBroken(spec, interface.IcdSyntaxError)
        
        # Same thing should happen with an empty ICD.
        self._testBroken("", interface.IcdSyntaxError)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.DEBUG)
    logging.getLogger("cutplace.test_icd").setLevel(logging.INFO)
    unittest.main()
