"""
Tests for `_ods`.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import Queue
import unittest

import dev_test
import _ods


class OdsTest(unittest.TestCase):

    def testConvertToCsv(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from__ods.csv")
        _ods.main([testInPath, testOutPath])

    def testConvertToDocBook(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from__ods.xml")
        _ods.main(["--format=docbook", testInPath, testOutPath])

    def testConvertToRst(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from__ods.rst")
        _ods.main(["--format=rst", testInPath, testOutPath])

    def testBrokenKinkyFileName(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("kinky_file_name//\\:^$\\::/")
        self.assertRaises(SystemExit, _ods.main, [testInPath, testOutPath])

    def testBrokenNoOptionsAtAll(self):
        self.assertRaises(SystemExit, _ods.main, [])

    def testBrokenSheet(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        testOutPath = dev_test.getTestOutputPath("valid_customers_from__ods.csv")
        self.assertRaises(SystemExit, _ods.main, ["--sheet=x", testInPath, testOutPath])
        self.assertRaises(SystemExit, _ods.main, ["--sheet=0", testInPath, testOutPath])
        # FIXME: Report error when sheet is out of range: self.assertRaises(SystemExit, _ods.main, ["--sheet=17", testInPath, testOutPath])

    def testConsumerProducer(self):
        testInPath = dev_test.getTestInputPath("valid_customers.ods")
        contentXmlReadable = _ods.odsContent(testInPath)
        rowQueue = Queue.Queue()
        producer = _ods.ProducerThread(contentXmlReadable, rowQueue)
        producer.start()
        hasRow = True
        while hasRow:
            row = rowQueue.get()
            if row is None:
                hasRow = False
        producer.join()

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace").setLevel(logging.INFO)
    logging.getLogger("cutplace.ods").setLevel(logging.INFO)
    unittest.main()
