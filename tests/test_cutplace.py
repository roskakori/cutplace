"""
Tests for cutplace application.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
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
import os
import unittest

from cutplace import dev_test
from cutplace import _cutplace
from cutplace import _ods

_log = logging.getLogger("cutplace")


class CutplaceTest(unittest.TestCase):
    """Test cases for cutplace command line interface."""
    def _test_process_exits_with(self, arguments, expected_exit_code):
        try:
            _cutplace.process(['test_cutplace.py'] + arguments)
            self.fail('SystemExit expected')
        except SystemExit as expected_error:
            self.assertEqual(expected_exit_code, expected_error.code)

    def test_can_show_version(self):
        self._test_process_exits_with(['--version'], 0)

    def test_can_show_help(self):
        self._test_process_exits_with(['--help'], 0)
        self._test_process_exits_with(['--h'], 0)

    def _test_can_read_cid(self, suffix):
        cid_path = dev_test.getTestIcdPath('customers.' + suffix)
        exit_code = _cutplace.process(['test_can_read_valid_' + suffix + '_cid', cid_path])
        self.assertEqual(0, exit_code)

    def test_can_read_csv_cid(self):
        source_ods_cid_path = dev_test.getTestIcdPath('customers.ods')
        target_csv_cid_path = dev_test.getTestIcdPath('customers.csv')
        _ods.toCsv(source_ods_cid_path, target_csv_cid_path)
        self._test_can_read_cid('csv')
        os.remove(target_csv_cid_path)

    # TODO #76: def test_can_read_ods_cid(self):
    #          self._test_can_read_cid('ods')

    def test_can_read_excel_cid(self):
        self._test_can_read_cid('xls')

    def test_fails_on_non_existent_cid(self):
        self.assertRaises(IOError, _cutplace.process, ['test_fails_on_non_existent_cid', 'no_such_cid.xls'])

    def test_can_validate_proper_csv(self):
        cid_path = dev_test.getTestIcdPath('customers.xls')
        csv_path = dev_test.getTestInputPath('valid_customers.csv')
        exit_code = _cutplace.process(['test_can_validate_proper_csv', cid_path, csv_path])
        self.assertEqual(0, exit_code)

    # TODO #76: After _tools.ods_rows() works, activate this.
    # def test_can_read_cid_with_plugins(self):
    #     cid_path = dev_test.getTestIcdPath('customers_with_plugins.ods')
    #     exit_code = _cutplace.process(['test_can_read_cid_with_plugins', '--plugins', dev_test.getTestPluginsPath(),
    #         cid_path])
    #     self.assertEqual(0, exit_code)
    #
    # def test_can_validate_proper_csv_with_plugins(self):
    #     cid_path = dev_test.getTestIcdPath('customers_with_plugins.ods')
    #     csv_path = dev_test.getTestInputPath('valid_customers.csv')
    #     exit_code = _cutplace.process(['test_can_validate_proper_csv_with_plugins', '--plugins',
    #         dev_test.getTestPluginsPath(), cid_path, csv_path])
    #     self.assertEqual(0, exit_code)

    def test_fails_on_non_existent_data(self):
        cid_path = dev_test.getTestIcdPath('customers.xls')
        self.assertRaises(IOError, _cutplace.process, ['test_fails_on_non_existent_data', cid_path, 'no_such_data.csv'])

    def test_fails_on_unknown_command_line_argument(self):
        self._test_process_exits_with(['--no-such-option'], 2)

    def test_fails_without_any_command_line_argument(self):
        self._test_process_exits_with([], 2)

    # TODO: Migrate test cases below.
    # def testValidCsvs(self):
    #     VALID_PREFIX = 'valid_'
    #     testsInputFolder = dev_test.getTestFolder('input')
    #     validCsvFileNames = _tools.listdirMatching(testsInputFolder, VALID_PREFIX + '.*\\.csv', '.*with_head.*')
    #     validCsvPaths = list(os.path.join(testsInputFolder, fileName) for fileName in validCsvFileNames)
    #     for dataPath in validCsvPaths:
    #         # Compute the base name of the related ICD.
    #         baseFileName = os.path.basename(dataPath)
    #         baseFileNameWithoutCsvSuffix = os.path.splitext(baseFileName)[0]
    #         baseFileNameWithoutValidPrefixAndCsvSuffix = baseFileNameWithoutCsvSuffix[len(VALID_PREFIX):]
    #         # Compute the full path of the related ICD.
    #         icdBaseName = baseFileNameWithoutValidPrefixAndCsvSuffix.split('_')[0]
    #         icdPath = dev_test.getTestIcdPath(icdBaseName + '.csv')
    #         if not os.path.exists(icdPath):
    #             icdPath = dev_test.getTestIcdPath(icdBaseName + '.ods')
    #             self.assertTrue(os.path.exists(icdPath),
    #                     'icd '%s' (or '*.csv') for data file '%s' must be created' % (icdPath, dataPath))
    #
    #         # Now validate the data.
    #         exitCode = _cutplace.main(['test_cutplace.py', icdPath, dataPath])
    #         self.assertEqual(exitCode, 0)
    #
    # def testValidFixedTxt(self):
    #     icdPath = dev_test.getTestIcdPath('customers_fixed.ods')
    #     dataPath = dev_test.getTestInputPath('valid_customers_fixed.txt')
    #     exitCode = _cutplace.main(['test_cutplace.py', icdPath, dataPath])
    #     self.assertEqual(exitCode, 0)
    #
    # def testValidNativeExcelFormats(self):
    #     icdPath = dev_test.getTestIcdPath('native_excel_formats.ods')
    #     dataPath = dev_test.getTestInputPath('valid_native_excel_formats.xls')
    #     exitCode = _cutplace.main(['test_cutplace.py', icdPath, dataPath])
    #     self.assertEqual(exitCode, 0)


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
