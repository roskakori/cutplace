# -*- coding: iso-8859-1 -*-
"""
Tests for interface control documents.
"""
import checks
import data
import dev_test
import fields
import interface
import logging
import parsers
import StringIO
import unittest

_log = logging.getLogger("cutplace.test_interface")

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
,Name,Type,Example,Empty,Length,Rule
F,branch_id,38123,RegEx,,5,38\d\d\d
F,customer_id,12345,Integer,,5,0:99999
F,first_name,John,Text,X,15
F,surname,Doe,Text,,15
F,gender,male,Choice,,7,"male, female, unknown"
F,date_of_birth,08.03.1957,DateTime,,10,DD.MM.YYYY
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

def createDefaultTestIcd(format, lineDelimiter="\n"):
    assert format in [data.FORMAT_CSV, data.FORMAT_EXCEL, data.FORMAT_ODS], "format=%r" % format
    assert lineDelimiter
    
    spec = ""","Interface: customer",,,,,
,,,,,,
,"Data format",,,,,
,,,,,,
"D","Format","%s",,,,
""" % format
    if format.lower() == data.FORMAT_CSV:
        spec += """"D","Line delimiter","LF",,,,
"D","Item delimiter",",",,,,
"D","Encoding","ISO-8859-1",,,,
"D","Allowed characters","32:",,,,
"""
    spec += """,,,,,,
,"Fields",,,,,
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","branch_id",38123,"RegEx",,,"38\d\d\d"
"F","customer_id",12345,"Integer",,,"0:99999"
"F","first_name","John","Text","X"
"F","surname","Doe","Text",,"1:60"
"F","gender","male","Choice",,,"female, male, other, unknown"
"F","date_of_birth",08.03.1957,"DateTime",,,"DD.MM.YYYY"
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
        createDefaultTestIcd(data.FORMAT_CSV, "\n")
        createDefaultTestIcd(data.FORMAT_CSV, "\r")
        createDefaultTestIcd(data.FORMAT_CSV, "\r\n")
        
    def testIsUniqueCheck(self):
        icd = createDefaultTestIcd(data.FORMAT_CSV)
        dataText = """38000,23,"John","Doe","male","08.03.1957"
38000,59,"Jane","Miller","female","04.10.1946"
38000,23,"Mike","Webster","male","23.12.1974" """
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)

    def testLatin1(self):
        icd = createDefaultTestIcd(data.FORMAT_CSV)
        dataText = """38000,23,"John","Doe","male","08.03.1957"
38000,59,"Bärbel","Müller","female","04.10.1946"
38000,23,"Mike","Webster","male","23.12.1974" """
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)
        
    def testSimpleFixedIcd(self):
        icd = createDefaultTestFixedIcd()
        dataText = "3800012345John           Doe            male   08.03.19573800012346Jane           Miller         female 04.10.1946"
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)

    def testValidOds(self):
        icd = createDefaultTestIcd(data.FORMAT_ODS)
        dataPath = dev_test.getTestInputPath("valid_customers.ods")
        icd.validate(dataPath)
        # TODO: Assert number of errors detected in dataPath is 0.

    def testValidExcel(self):
        icd = createDefaultTestIcd(data.FORMAT_EXCEL)
        dataPath = dev_test.getTestInputPath("valid_customers.xls")
        try:
            icd.validate(dataPath)
            # TODO: Assert number of errors detected in dataPath is 0.
        except parsers.CutplaceXlrdImportError:
            _log.warning("ignored ImportError caused by missing xlrd")


    def testEmptyChoice(self):
        spec = ""","Interface with a Choice field (gender) that can be empty"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","Text","X"
"F","gender","male","Choice",X,,"female, male"
"F","date_of_birth",08.03.1957,"DateTime",,,"DD.MM.YYYY"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)
    
    def testFieldTypeWithModule(self):
        spec = ""","Interface with field using a fully qualified type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","fields.Text","X"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)
    
    def testEmptyChoiceWithLength(self):
        spec = ""","Interface with a Choice field (gender) that can be empty and has a field length > 0"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","Text","X"
"F","gender","male","Choice",X,4:6,"female, male"
"F","date_of_birth",08.03.1957,"DateTime",,,"DD.MM.YYYY"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = """"John",,"08.03.1957"
"Jane","female","04.10.1946" """
        dataReadable = StringIO.StringIO(dataText)
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
        spec = ""","Broken Interface with data format specified after first field"
"F","branch_id",,"Text"
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
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","branch_id",,"RegEx",,,"38\d\d\d"
"F","","Integer",,,,"0:99999"
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        spec = ""","Broken Interface with missing field name"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","branch_id",,"RegEx",,,"38\d\d\d"
"F","     ",,"Integer",,,"0:99999"
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        
    def testBrokenFieldTypeMissing(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","branch_id",,"RegEx",,,"38\d\d\d"
"F","customer_id",,"",,,"0:99999"
"""
        self._testBroken(spec, fields.FieldSyntaxError)
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","branch_id",,"RegEx",,,"38\d\d\d"
"F","customer_id",,"     ",,,"0:99999"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmptyModule(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","first_name",,".Text","X",,,"John"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmptyClass(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","first_name",,"fields.","X"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWitEmtySubModule(self):
        spec = ""","Broken Interface with missing field type"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","first_name",,"fields..Text","X"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldNameWithInvalidCharacters(self):
        spec = ""","Broken Interface with field name containing invalid characters"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","först_name",,"Text","X"
"F","customer_id",,"",,,"0:99999"
"""
        self._testBroken(spec, fields.FieldSyntaxError)

    def testBrokenFieldTypeWithMultipleWord(self):
        spec = ""","Broken Interface with field type containing multiple words"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule","Example"
"F","first_name",,"Text and text again","X"
"F","customer_id",,"",,,"0:99999"
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

    def testBrokenInterfaceFieldExample(self):
        spec = ""","Interface with broken example for the gender field"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","Text","X"
"F","gender","spam","Choice",,4:6,"female, male"
"F","date_of_birth",08.03.1957,"DateTime",,,"DD.MM.YYYY"
"""
        self._testBroken(spec, interface.IcdSyntaxError)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    logging.getLogger("cutplace.test_interface").setLevel(logging.INFO)
    unittest.main()
