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

class _SimpleErrorLoggingIcdEventListener(interface.IcdEventListener):
    def _logError(self, row, errorMessage):
        _log.warning("error during validation: %s %r" % (str(errorMessage), row))
        
    def rejectedRow(self, row, errorMessage):
        self._logError(row, errorMessage)
    
    def checkAtRowFailed(self, row, errorMessage):
        self._logError(row, errorMessage)
    
    def checkAtEndFailed(self, errorMessage):
        self._logError(None, errorMessage)
    
    def dataFormatFailed(self, errorMessage):
        self._logError(None, errorMessage)

_defaultIcdListener = _SimpleErrorLoggingIcdEventListener()

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
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataPath)
            self.assertEqual(icd.rejectedCount, 0)
            self.assertEqual(icd.acceptedCount, 3)
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

        # TODO: Remove the line below once icd.validate() calls reset().
        icd = createDefaultTestIcd(data.FORMAT_ODS)
        icd.dataFormat.set(data.KEY_SHEET, 2)
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataPath)
            self.assertEqual(icd.rejectedCount, 0)
            self.assertEqual(icd.acceptedCount, 4)
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

    def testValidExcel(self):
        icd = createDefaultTestIcd(data.FORMAT_EXCEL)
        dataPath = dev_test.getTestInputPath("valid_customers.xls")
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataPath)
            self.assertEqual(icd.rejectedCount, 0)
            self.assertEqual(icd.acceptedCount, 3)
        except parsers.CutplaceXlrdImportError:
            _log.warning("ignored ImportError caused by missing xlrd")
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

        # TODO: Remove the line below once icd.validate() calls reset().
        icd = createDefaultTestIcd(data.FORMAT_EXCEL)
        icd.dataFormat.set(data.KEY_SHEET, 2)
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataPath)
            self.assertEqual(icd.rejectedCount, 0)
            self.assertEqual(icd.acceptedCount, 4)
        except parsers.CutplaceXlrdImportError:
            _log.warning("ignored ImportError caused by missing xlrd")
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

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
        dataText = """"John"
Jane"""
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

    def testBrokenDataFormatTooSmallHeader(self):
        spec = ""","Broken Interface with invalid data format where the header is too small"
"D","Format","CSV"
"D","Header","-1"
"""
        self._testBroken(spec, data.DataFormatSyntaxError)
        
    def testBrokenDataFormatNonNumericHeader(self):
        spec = ""","Broken Interface with invalid data format where the header is too small"
"D","Format","CSV"
"D","Header","eggs"
"""
        self._testBroken(spec, data.DataFormatSyntaxError)
        
    def testBrokenDataFormatInvalidFormatPropertyName(self):
        spec = ""","Broken Interface with broken name for format property"
"D","Fromat","CSV"
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

    def testTooManyItems(self):
        spec = ""","Interface with a single field"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","Text","X"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = "John, Doe"
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)
        self.assertEqual(icd.rejectedCount, 1)

    def testLastOptionalField(self):
        spec = ""","Interface with two fields with the second being optional"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","customer_id",,Integer,,,0:
"F","first_name","John","Text","X"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = """123,John
234,
"""
        dataReadable = StringIO.StringIO(dataText)
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataReadable)
            self.assertEqual(icd.acceptedCount, 2)
            self.assertEqual(icd.rejectedCount, 0)
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

    def testTooFewItems(self):
        spec = ""","Interface with two fields with the second being required"
"D","Format","CSV"
"D","Line delimiter","LF"
"D","Item delimiter",","
"D","Encoding","ISO-8859-1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","customer_id",,Integer,,,0:
"F","first_name","John","Text"
"""
        # Test that a specifically empty item is rejected.
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = "123,"
        dataReadable = StringIO.StringIO(dataText)
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataReadable)
            self.assertEqual(icd.acceptedCount, 0)
            self.assertEqual(icd.rejectedCount, 1)
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

        # Test that a missing item is rejected.
        dataText = "234"
        dataReadable = StringIO.StringIO(dataText)
        icd.addIcdEventListener(_defaultIcdListener)
        try:
            icd.validate(dataReadable)
            self.assertEqual(icd.acceptedCount, 0)
            self.assertEqual(icd.rejectedCount, 1)
        finally:
            icd.removeIcdEventListener(_defaultIcdListener)

    def testSkipHeader(self):
        spec = ""","Interface for data with header rows"
"D","Format","CSV"
"D","Line delimiter","Any"
"D","Item delimiter",","
"D","Header","1"
,,,,,,
,"Name","Example","Type","Empty","Length","Rule"
"F","first_name","John","Text","X"
"F","gender","male","Choice",X,,"female, male"
"F","date_of_birth",08.03.1957,"DateTime",,,"DD.MM.YYYY"
"""
        icd = interface.InterfaceControlDocument()
        icd.read(StringIO.StringIO(spec))
        dataText = """First Name,Gender,Date of birth
John,male,08.03.1957
Mike,male,23.12.1974"""
        dataReadable = StringIO.StringIO(dataText)
        icd.validate(dataReadable)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.DEBUG)
    logging.getLogger("cutplace.test_interface").setLevel(logging.DEBUG)
    unittest.main()
