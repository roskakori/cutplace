"""
Development tool and utility functions for testing and test data generation.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    """
    Path of `folder` in tests folder.
    """
    assert folder
    
    # Attempt to find `folder` in "tests" folder based from current folder.
    testFolder = os.path.join(os.getcwd(), "tests")
    if not os.path.exists(testFolder) and (len(sys.argv) == 2):
        # Try the folder specified in the one and only command line option.
        # TODO: Make the base folder a property setable from outside. 
        testFolder = os.path.join(sys.argv[1], "tests")
    if not os.path.exists(testFolder):
        basePath = os.getcwd()
        testFolderfound = False
        while not testFolderfound and basePath:
            basePath = os.path.split(basePath)[0]
            testFolder = os.path.join(basePath, "tests")
            testFolderfound = os.path.exists(testFolder)
    if not os.path.exists(testFolder):
        raise IOError("cannot find test folder: test must run from project folder or project folder must be passed as command line option; currently attempting to find test folder in: %r" % testFolder)
    result = os.path.join(testFolder, folder)
    return result
    
def getTestFile(folder, fileName):
    """
    Path of file `fileName` in `folder` located in tests folder.
    """
    assert folder
    assert fileName
    
    result = os.path.join(getTestFolder(folder), fileName)
    return result

def getTestInputPath(fileName):
    """
    Path for test file `fileName` in input folder.
    """
    assert fileName
    return getTestFile("input", fileName)

def getTestOutputPath(fileName):
    """
    Path for test file `fileName` in output folder.
    """
    assert fileName
    return getTestFile("output", fileName)

def getTestIcdPath(fileName):
    """
    Path for test ICD `fileName`which has to be located in "tests/input/icds".
    """
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
    """
    Create "customers.csv" from "customers.ods".
    """
    sourceOdsPath = getTestIcdPath("customers.ods")
    targetCsvPath = getTestIcdPath("customers.csv")
    ods.toCsv(sourceOdsPath, targetCsvPath)

def createLotsOfCustomersCsv(targetCsvPath):
    # TODO: Use a random seed to generate the same data every time.
    assert targetCsvPath is not None
    
    targetCsvFile = open(targetCsvPath, "w")
    _log.info("write lots of customers to %r" % targetCsvPath)
    try:
        csvWriter = csv.writer(targetCsvFile)
        for customerId in range(1000):
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
        