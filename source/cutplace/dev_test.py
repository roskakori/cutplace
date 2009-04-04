"""Devlopment tool to generate testdate for cutplace tests."""
import csv
import logging
import ods
import optparse
import os
import random
import sys
import tools

_log = logging.getLogger("cutplace.dev_test")

def getTestFolder(folder):
    """Path of "folder" in tests folder."""
    assert folder
    
    # Try current folder.
    testFolder = os.path.join(os.getcwd(), "tests")
    if not os.path.exists(testFolder) and (len(sys.argv) == 2):
        # Try the folder specified in the one and only command line option.
        # TODO: Make the base folder a property setable from outside. 
        testFolder = os.path.join(sys.argv[1], "tests")
    if not os.path.exists(testFolder):
        raise IOError("cannot find test folder: test must run from project folder or project folder must be passed as command line option; currently attempting to find test folder in: %r" % testFolder)
    result = os.path.join(testFolder, folder)
    return result
    
def getTestFile(folder, fileName):
    """Path of "folder" and "fileName" in tests folder."""
    assert folder
    assert fileName
    
    result = os.path.join(getTestFolder(folder), fileName)
    return result

def getTestInputPath(fileName):
    """Get path for test file in input folder."""
    assert fileName
    return getTestFile("input", fileName)

def getTestIcdPath(fileName):
    """Get path for test ICD."""
    assert fileName
    return getTestFile(os.path.join("input", "icds"), fileName)

def getLotsOfCustomersCsvPath():
    return getTestInputPath("lots_of_customers.csv")

def createTestCustomerRow(customerId):
    global _customerId
    
    branchId = random.choice(["38000", "38053", "38111"])
    isMale = random.choice([True, False])
    firstName = tools.createTestFirstName(isMale)
    surname = tools.createTestSurname()
    if random.randint(0, 100) == 50:
        gender = "unknown"
    elif isMale:
        gender = "male"
    else:
        gender = "female"
    dateOfBirth = tools.createTestDateTime("%d.%m.%Y")
    return [branchId, customerId, firstName, surname, gender, dateOfBirth]

def createIcdsCustomerCsv():
    sourceOdsPath = getTestIcdPath("customers.ods")
    targetCsvPath = getTestIcdPath("customers.csv")
    ods.toCsv(sourceOdsPath, targetCsvPath)

def createLotsOfCustomersCsv(targetCsvPath):
    # TODO: Use a randome seed to generate the same data every time.
    assert targetCsvPath is not None
    
    targetCsvFile = open(targetCsvPath, "w")
    _log.info("write lots of customers to %r" % targetCsvPath)
    try:
        csvWriter = csv.writer(targetCsvFile)
        for customerId in range(0, 1000):
            csvWriter.writerow(createTestCustomerRow(customerId))
    finally:
        targetCsvFile.close()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)

    usage = "usage: %prog"
    parser = optparse.OptionParser(usage)
    options, others = parser.parse_args()
    if len(others) == 0:
        createIcdsCustomerCsv()
        createLotsOfCustomersCsv(getLotsOfCustomersCsvPath())
    else:
        sys.stderr.write("unknown option must be removed: %r%s" % (others[0], os.linesep))
        sys.exit(1)
        